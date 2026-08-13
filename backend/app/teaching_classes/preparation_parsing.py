"""备课解析编排模块：文档解析编排、状态管理和后台解析执行。

从 PreparationSessionModule 提取，聚合备课会话解析相关的业务逻辑。
"""
from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from app.database import Database
from app.document_parsing import CourseContentParsing, ParsingError, ParsingStatus
from app.teaching_classes.models import (
    CurrentStep,
    FileFormat,
    ParseStatus,
)

logger = logging.getLogger("course_agent.preparation_sessions")

BackgroundExecutor = "collections.abc.Callable[[collections.abc.Callable[[], None]], None]"


class ParsingOrchestrator:
    """备课解析编排：触发解析、后台执行、状态管理。"""

    def __init__(
        self,
        database: Database,
        now_provider,
        course_content_parsing: CourseContentParsing,
        background_executor,
        upload_root: Path,
    ) -> None:
        self._database = database
        self._now = now_provider
        self._course_content_parsing = course_content_parsing
        self._background_executor = background_executor
        self._upload_root = upload_root

    def execute_parse_background(self, session_id: str, storage_key: str, file_format: FileFormat) -> None:
        """在独立线程中启动解析（连接状态已在调用方更新）。"""
        self._background_executor(
            lambda: self._run_parse(session_id, storage_key, file_format)
        )

    def _run_parse(self, session_id: str, storage_key: str, file_format: FileFormat) -> None:
        """后台线程只记录受控错误码，不记录任何文档内容。"""
        try:
            with self._database.connect() as connection:
                row = connection.execute(
                    "SELECT storage_key FROM preparation_sessions WHERE id=?",
                    (session_id,),
                ).fetchone()
            if row is None or row["storage_key"] != storage_key:
                return

            result = self._course_content_parsing.parse(
                self._upload_root / storage_key, file_format
            )
            now = self._now()
            with self._database.connect() as connection:
                current = connection.execute(
                    """SELECT storage_key, parse_status
                       FROM preparation_sessions WHERE id=?""",
                    (session_id,),
                ).fetchone()
                if (current is None
                        or current["storage_key"] != storage_key
                        or current["parse_status"] != ParseStatus.PARSING.value):
                    return

                connection.execute(
                    "DELETE FROM preparation_session_segments WHERE session_id=?", (session_id,)
                )
                if result.status is ParsingStatus.COMPLETED:
                    connection.executemany(
                        """INSERT INTO preparation_session_segments
                           (session_id, ordinal, document_id, chunk_id, document_version,
                            block_type, content, created_at)
                           VALUES (?, ?, NULL, NULL, NULL, ?, ?, ?)""",
                        [
                            (session_id, item.order, item.block_type, item.content, now)
                            for item in result.paragraphs
                        ],
                    )
                    connection.execute(
                        """UPDATE preparation_sessions
                           SET parse_status=?, current_step=?, parse_completed_at=?, updated_at=?
                           WHERE id=?""",
                        (ParseStatus.COMPLETED.value, CurrentStep.HIGHLIGHTING.value, now, now, session_id),
                    )
                else:
                    state = (
                        ParseStatus.TIMED_OUT.value
                        if result.status is ParsingStatus.TIMED_OUT
                        else ParseStatus.FAILED.value
                    )
                    error_code = "PARSING_TIMED_OUT" if state == ParseStatus.TIMED_OUT.value else "PARSING_FAILED"
                    logger.warning(
                        "preparation_session_parse_failed session_id=%s parse_status=%s error_code=%s error_message=%s",
                        session_id, state, error_code, result.error_message or "解析器返回失败结果",
                    )
                    connection.execute(
                        """UPDATE preparation_sessions
                           SET parse_status=?, current_step=?, parse_error_code=?,
                               parse_completed_at=?, updated_at=?
                           WHERE id=?""",
                        (state, CurrentStep.UPLOAD.value, error_code, now, now, session_id),
                    )
        except ParsingError as error:
            logger.warning(
                "preparation_session_parse_failed session_id=%s error_code=%s error_message=%s",
                session_id, error.code, error.message,
            )
            self._record_parse_failure(session_id, error.code)
        except Exception as error:
            logger.exception(
                "preparation_session_parse_failed session_id=%s error_type=%s",
                session_id, type(error).__name__,
            )
            self._record_parse_failure(session_id, "PARSING_FAILED")

    def _record_parse_failure(self, session_id: str, error_code: str) -> None:
        """保留解析适配器稳定错误码，不把内部异常文本写入数据库。"""
        now = self._now()
        with self._database.connect() as connection:
            connection.execute(
                "DELETE FROM preparation_session_segments WHERE session_id=?", (session_id,),
            )
            connection.execute(
                """UPDATE preparation_sessions
                   SET parse_status=?, current_step=?, parse_error_code=?,
                       parse_completed_at=?, updated_at=?
                   WHERE id=?""",
                (ParseStatus.FAILED.value, CurrentStep.UPLOAD.value, error_code, now, now, session_id),
            )
