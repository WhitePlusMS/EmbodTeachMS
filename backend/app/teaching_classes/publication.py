import logging
import sqlite3
import uuid
from collections.abc import Callable

from app.auth.models import UserView
from app.common.errors import BusinessError
from app.database import Database
from app.teaching_classes.access import TeachingClassAccess
from app.teaching_classes.course_content_publisher import CourseContentPublisher
from app.teaching_classes.models import (
    CurrentStep,
    PreparationSessionView,
    PublishHomeworkRequest,
    PublishHomeworkResponse,
)
from app.teaching_classes.preparation_sessions import PreparationSessionRecords
from app.teaching_classes.preparation_state import (
    PreparationSessionStateStore,
    PublicationDraft,
)
from app.teaching_classes.question_review import QuestionReviewModule

logger = logging.getLogger("course_agent.publication")


class PublicationModule:
    """发布验证服务，集中验证发布条件、教师权限和幂等性"""

    def __init__(
        self,
        database: Database,
        now_provider: Callable[[], int],
        publisher: CourseContentPublisher,
        records: PreparationSessionRecords | None = None,
        state_store: PreparationSessionStateStore | None = None,
        question_review: QuestionReviewModule | None = None,
    ) -> None:
        self._database = database
        self._now = now_provider
        self._publisher = publisher
        self._access = TeachingClassAccess()
        self._records = records or PreparationSessionRecords()
        self._state = state_store or PreparationSessionStateStore()
        self._question_review = question_review or QuestionReviewModule()

    def validate_publication_conditions(
        self, class_id: str, teacher: UserView, is_homework: bool = False
    ) -> tuple[PreparationSessionView, list[dict]]:
        """公开只读校验入口；发布写路径使用同事务内的私有校验。"""
        with self._database.connect() as connection:
            row, questions = self._validate_in_transaction(
                connection, class_id, teacher, is_homework
            )
            return self._records.to_view(row), questions

    def _validate_in_transaction(
        self,
        connection: sqlite3.Connection,
        class_id: str,
        teacher: UserView,
        is_homework: bool,
    ) -> tuple[sqlite3.Row, list[dict]]:
        """在调用方持有的事务中验证全部发布不变量。"""
        self._access.require_owned_class(connection, class_id, teacher)
        row = self._records.find(connection, class_id)
        if row is None:
            raise BusinessError(
                status_code=404,
                code="PREPARATION_SESSION_NOT_FOUND",
                message="备课会话不存在",
            )
        if self._state.load_publication_draft(connection, row["id"]).get("published_at"):
            raise BusinessError(
                status_code=409,
                code="PUBLICATION_ALREADY_EXISTS",
                message="此备课会话已发布，不能重复发布",
            )
        session = self._records.to_view(row)
        if session.parse_status.value != "completed":
            raise BusinessError(
                status_code=400,
                code="PREPARATION_SESSION_NOT_PARSED",
                message="备课会话未完成解析，无法发布",
            )
        if session.current_step.value not in {"highlighting", "questioning", "publishing"}:
            raise BusinessError(
                status_code=400,
                code="INVALID_PUBLICATION_STEP",
                message="当前步骤不允许发布，请先完成题目编辑",
            )
        questions = self._state.load_questions(connection, row["id"])
        if not self._question_review.is_publish_unlocked(questions):
            raise BusinessError(
                status_code=400,
                code="PUBLICATION_NOT_UNLOCKED",
                message="题目未完成审核，无法发布",
            )
        if is_homework and not any(
            question.get("review_status") == "confirmed" for question in questions
        ):
            raise BusinessError(
                status_code=400,
                code="HOMEWORK_PUBLICATION_NO_CONFIRMED_QUESTIONS",
                message="发布作业必须至少有一个确认题",
            )
        logger.info(
            "publication_conditions_validated class_id=%s teacher_id=%s session_id=%s is_homework=%s",
            class_id,
            teacher.id,
            session.id,
            is_homework,
        )
        return row, questions

    def publish(self, class_id: str, teacher: UserView) -> PreparationSessionView:
        """以单连接写事务发布课程内容，幂等校验与写入不可分割。"""
        try:
            with self._database.connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                row, _ = self._validate_in_transaction(
                    connection, class_id, teacher, False
                )
                content_ids: list[str] = []
                self.mark_publication_in_progress(connection, row["id"], content_ids)
                content_ids = self._publisher.publish_course_content(
                    connection, row, class_id
                )
                self._record_knowledge_base_snapshot(connection, row, class_id, content_ids)
                self.mark_publication_completed(connection, row["id"], content_ids)
                updated = self._records.find(connection, class_id)
                if updated is None:
                    raise RuntimeError("发布事务完成后备课会话缺失")
                return self._records.to_view(updated)
        except BusinessError:
            raise
        except Exception as error:
            logger.exception(
                "publication_failed class_id=%s teacher_id=%s",
                class_id,
                teacher.id,
            )
            raise BusinessError(
                status_code=500,
                code="PUBLICATION_FAILED",
                message="发布失败，请稍后重试",
            ) from error

    def _record_knowledge_base_snapshot(
        self,
        connection: sqlite3.Connection,
        session_row: sqlite3.Row,
        class_id: str,
        content_ids: list[str],
    ) -> None:
        """记录备课发布时的知识库文档版本，课程内容本身仍是独立快照。"""
        knowledge_base_id = session_row["knowledge_base_id"]
        if not knowledge_base_id:
            return
        selected_rows = connection.execute(
            """
            SELECT document_id, document_version
            FROM preparation_session_documents
            WHERE session_id = ?
            ORDER BY ordinal
            """,
            (session_row["id"],),
        ).fetchall()
        versions: dict[str, int] = {}
        if selected_rows:
            versions = {row["document_id"]: row["document_version"] for row in selected_rows}
        previous = connection.execute(
            "SELECT COALESCE(MAX(version), 0) FROM course_publications WHERE knowledge_base_id = ?",
            (knowledge_base_id,),
        ).fetchone()[0]
        connection.execute(
            """
            INSERT INTO course_publications
                (id, knowledge_base_id, class_id, version, preparation_session_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                knowledge_base_id,
                class_id,
                int(previous) + 1,
                session_row["id"],
                self._now(),
            ),
        )
        # UUID 主键无法从 last_insert_rowid 获取，按知识库版本取本次记录。
        publication_id = connection.execute(
            "SELECT id FROM course_publications WHERE knowledge_base_id = ? AND version = ?",
            (knowledge_base_id, int(previous) + 1),
        ).fetchone()[0]
        connection.executemany(
            "INSERT INTO course_publication_contents(publication_id, content_id, ordinal) VALUES (?, ?, ?)",
            [(publication_id, content_id, ordinal) for ordinal, content_id in enumerate(content_ids)],
        )
        connection.executemany(
            "INSERT INTO course_publication_documents(publication_id, document_id, document_version) VALUES (?, ?, ?)",
            [(publication_id, document_id, version) for document_id, version in versions.items()],
        )

    def publish_homework(
        self,
        class_id: str,
        request: PublishHomeworkRequest,
        teacher: UserView,
    ) -> PublishHomeworkResponse:
        """以单连接写事务发布作业并直接返回本次创建的作业 ID。"""
        self.validate_homework_fields(request.title, request.due_at, self._now())
        try:
            with self._database.connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                row, _ = self._validate_in_transaction(
                    connection, class_id, teacher, True
                )
                self.mark_publication_in_progress(connection, row["id"], [])
                result = self._publisher.publish_homework(
                    connection,
                    row,
                    class_id,
                    request.title,
                    request.due_at,
                    request.description,
                )
                self.mark_publication_completed(
                    connection, row["id"], result["content_ids"]
                )
                updated = self._records.find(connection, class_id)
                if updated is None:
                    raise RuntimeError("作业发布事务完成后备课会话缺失")
                return PublishHomeworkResponse(
                    session=self._records.to_view(updated),
                    homework_id=result["homework_id"],
                )
        except BusinessError:
            raise
        except Exception as error:
            logger.exception(
                "homework_publication_failed class_id=%s teacher_id=%s",
                class_id,
                teacher.id,
            )
            raise BusinessError(
                status_code=500,
                code="HOMEWORK_PUBLICATION_FAILED",
                message="作业发布失败，请稍后重试",
            ) from error

    def validate_homework_fields(
        self, title: str, due_at: int, now: int
    ) -> None:
        """验证作业字段合法性"""
        # 验证标题非空
        if not title or not title.strip():
            raise BusinessError(
                status_code=400,
                code="HOMEWORK_TITLE_REQUIRED",
                message="作业标题不能为空",
            )

        # 验证截止时间大于当前时间
        if due_at <= now:
            raise BusinessError(
                status_code=400,
                code="HOMEWORK_DUE_AT_INVALID",
                message="作业截止时间必须大于当前时间",
            )

    def mark_publication_in_progress(
        self, connection: sqlite3.Connection, session_id: str, course_content_ids: list[str]
    ) -> None:
        """标记发布进行中状态"""
        now = self._now()
        publication_draft: PublicationDraft = {
            "published_at": None,  # 发布中状态，尚未完成
            "course_content_ids": course_content_ids,
        }
        self._state.save_publication_draft(connection, session_id, publication_draft, now)

        logger.info(
            "publication_marked_in_progress session_id=%s course_content_count=%d",
            session_id,
            len(course_content_ids),
        )

    def mark_publication_completed(
        self, connection: sqlite3.Connection, session_id: str, course_content_ids: list[str]
    ) -> None:
        """标记发布完成状态"""
        now = self._now()
        publication_draft: PublicationDraft = {
            "published_at": now,
            "course_content_ids": course_content_ids,
        }
        self._state.save_publication_draft(
            connection,
            session_id,
            publication_draft,
            now,
            current_step=CurrentStep.PUBLISHING.value,
        )

        logger.info(
            "publication_completed session_id=%s course_content_count=%d",
            session_id,
            len(course_content_ids),
        )
