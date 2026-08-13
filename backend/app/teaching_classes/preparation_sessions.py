"""备课会话管理 Facade 模块。

作为备课会话的窄接口 Facade，组合内部子模块：
- UploadManager（在 preparation_upload.py）：文件验证
- ParsingOrchestrator（在 preparation_parsing.py）：解析编排
- HighlightManager（在 preparation_highlights.py）：教学重点管理
- QuestionManager（在 preparation_questions.py）：题目管理

外部代码只通过此 Facade 或 __init__ 暴露的 exports 与备课模块交互。
"""
from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from collections.abc import Callable
from pathlib import Path
from threading import Thread

from app.auth.models import UserView
from app.common.errors import BusinessError
from app.database import Database
from app.document_parsing import CourseContentParsing, ParsingError, ParsingStatus
from app.knowledge_bases.service import KnowledgeBaseService
from app.llm_gateway import (
    ChatGateway,
    ChatGatewayRequest,
    UnconfiguredChatGateway,
    filter_sensitive_text,
)
from app.teaching_classes.access import TeachingClassAccess
from app.teaching_classes.models import (
    AddHighlightRequest,
    CandidateQuestionGenerationView,
    ConfirmCandidateQuestionRequest,
    CreateQuestionRequest,
    CurrentStep,
    DeleteQuestionRequest,
    FileFormat,
    ParseStatus,
    QuestionListView,
    QuestionView,
    UpdateQuestionRequest,
    HighlightView,
    PreparationSessionParagraphView,
    PreparationSessionParsingResultWithHighlightsView,
    PreparationSessionView,
    RemoveHighlightRequest,
    SelectPreparationDocumentsRequest,
    UploadStatus,
)
from app.teaching_classes.preparation_state import PreparationSessionStateStore
from app.teaching_classes.question_review import QuestionReviewModule, StoredQuestion
from app.teaching_classes.preparation_highlights import HighlightManager
from app.teaching_classes.preparation_parsing import ParsingOrchestrator
from app.teaching_classes.preparation_questions import QuestionManager
from app.teaching_classes.preparation_upload import (
    validate_file_content,
    generate_storage_key,
)


logger = logging.getLogger("course_agent.preparation_sessions")

BackgroundExecutor = Callable[[Callable[[], None]], None]


def run_in_daemon_thread(task: Callable[[], None]) -> None:
    """生产后台执行器；测试可注入同步执行器而不 patch 类成员。"""
    Thread(target=task, daemon=True).start()


class PreparationSessionRecords:
    """备课会话持久化 module，集中记录读取与 DTO 映射。"""

    _SELECT = """
        SELECT id, class_id, owner_teacher_id, original_filename, file_format,
               file_size_bytes, upload_status, parse_status, current_step, storage_key,
               parse_error_code, parse_started_at, parse_completed_at,
               parsed_content_reference, knowledge_base_id,
               state_revision,
               COALESCE((SELECT json_group_array(document_id ORDER BY ordinal)
                         FROM preparation_session_documents
                         WHERE session_id = preparation_sessions.id), '[]') AS selected_document_ids_json,
               COALESCE((SELECT json_group_array(json_object(
                   'id', id, 'paragraphOrdinal', segment_ordinal,
                   'startOffset', start_offset, 'endOffset', end_offset,
                   'createdAt', created_at
               )) FROM (
                   SELECT id, segment_ordinal, start_offset, end_offset, created_at
                   FROM preparation_highlights WHERE session_id = preparation_sessions.id
                   ORDER BY segment_ordinal, start_offset, end_offset, id
               )), '[]') AS highlights_json,
               COALESCE((SELECT json_group_array(json_object(
                   'id', id, 'source', source, 'review_status', review_status,
                   'type', question_type, 'stem', stem,
                   'options', json(options_json),
                   'correct_answers', json(correct_answers_json),
                   'knowledge_points', json(knowledge_points_json),
                   'highlight_source_ids', json(highlight_source_ids_json),
                   'hint', hint, 'explanation', explanation,
                   'created_at', created_at, 'updated_at', updated_at
               )) FROM (
                   SELECT id, source, review_status, question_type, stem,
                          options_json, correct_answers_json, knowledge_points_json,
                          highlight_source_ids_json, hint, explanation,
                          created_at, updated_at
                   FROM preparation_questions WHERE session_id = preparation_sessions.id
                   ORDER BY created_at, id
               )), '[]') AS candidate_questions_json,
               json_object(
                   'published_at', published_at,
                   'course_content_ids', json(
                       CASE WHEN EXISTS (
                           SELECT 1 FROM course_publications cp
                           WHERE cp.preparation_session_id = preparation_sessions.id
                       ) THEN COALESCE((SELECT json_group_array(content_id) FROM (
                           SELECT cpc.content_id
                           FROM course_publication_contents cpc
                           JOIN course_publications cp ON cp.id = cpc.publication_id
                           WHERE cp.preparation_session_id = preparation_sessions.id
                           ORDER BY cpc.ordinal
                       )), '[]') ELSE published_content_ids_json END
                   )
               ) AS publication_draft_json,
               created_at, updated_at
        FROM preparation_sessions
        WHERE class_id = ?
    """

    def find(self, connection: sqlite3.Connection, class_id: str) -> sqlite3.Row | None:
        """按教学班读取唯一活动会话。"""
        row = connection.execute(self._SELECT, (class_id,)).fetchone()
        if row is None or row["id"] is None:
            return None
        return row

    def to_view(self, row: sqlite3.Row) -> PreparationSessionView:
        """将 SQLite 记录转换为唯一的对外 DTO。"""
        publication_draft = row["publication_draft_json"]
        if publication_draft:
            try:
                parsed_draft = json.loads(publication_draft)
                if not parsed_draft.get("published_at") and not parsed_draft.get("course_content_ids"):
                    publication_draft = "{}"
            except json.JSONDecodeError:
                publication_draft = "{}"
        return PreparationSessionView(
            id=row["id"],
            class_id=row["class_id"],
            original_filename=row["original_filename"],
            file_format=FileFormat(row["file_format"]) if row["file_format"] else None,
            file_size_bytes=row["file_size_bytes"],
            upload_status=UploadStatus(row["upload_status"]),
            parse_status=ParseStatus(row["parse_status"]),
            current_step=CurrentStep(row["current_step"]),
            parsed_content_reference=row["parsed_content_reference"],
            parse_error_code=row["parse_error_code"],
            parse_started_at=row["parse_started_at"],
            parse_completed_at=row["parse_completed_at"],
            highlights_json=row["highlights_json"],
            candidate_questions_json=row["candidate_questions_json"],
            publication_draft_json=publication_draft,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            knowledge_base_id=row["knowledge_base_id"],
            selected_document_ids=json.loads(row["selected_document_ids_json"] or "[]"),
        )


class PreparationSessionModule:
    """备课会话的单一 interface，封装文件、解析、段落和重点的完整生命周期。"""

    def __init__(
        self,
        database: Database,
        now_provider: Callable[[], int],
        course_content_parsing: CourseContentParsing,
        background_executor: BackgroundExecutor,
        knowledge_base_service: KnowledgeBaseService,
        chat_gateway: ChatGateway | None = None,
        records: PreparationSessionRecords | None = None,
        state_store: PreparationSessionStateStore | None = None,
        question_review: QuestionReviewModule | None = None,
    ) -> None:
        self._database = database
        self._now = now_provider
        self._access = TeachingClassAccess()
        self._records = records or PreparationSessionRecords()
        self._state = state_store or PreparationSessionStateStore()
        self._question_review = question_review or QuestionReviewModule()
        self._upload_root = database.path.parent / "private_uploads"
        self._course_content_parsing = course_content_parsing
        self._background_executor = background_executor
        self._knowledge_base_service = knowledge_base_service
        self._chat_gateway = chat_gateway or UnconfiguredChatGateway()

        # 子模块
        self._highlight_manager = HighlightManager(now_provider)
        self._parsing_orchestrator = ParsingOrchestrator(
            database, now_provider, course_content_parsing, background_executor, self._upload_root
        )
        self._question_manager = QuestionManager(now_provider, self._chat_gateway)

    # ── 会话 CRUD ──────────────────────────────────────────────

    def _require_session(
        self, connection: sqlite3.Connection, class_id: str, teacher: UserView,
    ) -> sqlite3.Row:
        """鉴权 + 查找会话 + 非空检查，消除重复样板。"""
        self._access.require_owned_class(connection, class_id, teacher)
        session = self._records.find(connection, class_id)
        if session is None:
            raise BusinessError(status_code=404, code="PREPARATION_SESSION_NOT_FOUND", message="备课会话不存在")
        return session

    def get_or_create_preparation_session(
        self, class_id: str, teacher: UserView
    ) -> tuple[PreparationSessionView, bool]:
        """获取或创建备课会话"""
        now = self._now()
        with self._database.connect() as connection:
            self._access.require_owned_class(connection, class_id, teacher)
            existing_session = self._records.find(connection, class_id)
            if existing_session:
                return self._records.to_view(existing_session), False

            session_id = str(uuid.uuid4())
            connection.execute(
                """INSERT INTO preparation_sessions (
                    id, class_id, owner_teacher_id, upload_status, parse_status,
                    current_step, knowledge_base_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?)""",
                (session_id, class_id, teacher.id, UploadStatus.WAITING.value,
                 ParseStatus.NOT_STARTED.value, CurrentStep.UPLOAD.value, now, now),
            )
            logger.info("preparation_session_created session_id=%s class_id=%s", session_id, class_id)
            return PreparationSessionView(
                id=session_id, class_id=class_id, original_filename=None,
                file_format=None, file_size_bytes=None, upload_status=UploadStatus.WAITING,
                parse_status=ParseStatus.NOT_STARTED, current_step=CurrentStep.UPLOAD,
                parsed_content_reference=None, highlights_json="[]",
                candidate_questions_json="[]", publication_draft_json="{}",
                created_at=now, updated_at=now, knowledge_base_id=None,
                selected_document_ids=[],
            ), True

    def get_preparation_session(self, class_id: str, teacher: UserView) -> PreparationSessionView:
        """获取备课会话"""
        with self._database.connect() as connection:
            session = self._require_session(connection, class_id, teacher)
            return self._records.to_view(session)

    # ── 分段规则标签 ──────────────────────────────────────────

    @staticmethod
    def _segment_rule_label(settings: sqlite3.Row) -> str:
        if settings["mode"] == "simple":
            return "简单分段 · 按文档结构"
        try:
            raw_separators = json.loads(settings["separators_json"] or "[]")
        except (TypeError, ValueError):
            logger.warning("preparation_invalid_segment_settings kb=%s", settings["knowledge_base_id"])
            raw_separators = []
        separators = [s for s in raw_separators if isinstance(s, str) and s]
        sep = separators[0] if separators else "#"
        labels = {"#": "一级标题", "##": "二级标题", "###": "三级标题", "。": "句号", "，": "逗号", "；": "分号"}
        return f"{sep} · {labels.get(sep, '自定义分隔符')}"

    # ── 知识库文档选择 ──────────────────────────────────────────

    def select_knowledge_base_documents(
        self, class_id: str, request: SelectPreparationDocumentsRequest, teacher: UserView,
    ) -> PreparationSessionView:
        """把班级知识库已完成文档装载为备课段落。"""
        now = self._now()
        selected_ids = list(dict.fromkeys(request.document_ids))
        with self._database.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            session = self._require_session(connection, class_id, teacher)
            if not selected_ids:
                self._clear_relationship_state(connection, session["id"])
                connection.execute(
                    """UPDATE preparation_sessions
                       SET original_filename=NULL, file_format=NULL, file_size_bytes=NULL,
                           upload_status='waiting', parse_status='not_started', current_step='upload',
                           storage_key=NULL, parse_error_code=NULL, parse_started_at=NULL,
                           parse_completed_at=NULL, parsed_content_reference=NULL,
                           knowledge_base_id=NULL, updated_at=?
                       WHERE id=?""",
                    (now, session["id"]),
                )
                updated = self._records.find(connection, class_id)
                if updated is None:
                    raise RuntimeError("退出备课文档后会话缺失")
                return self._records.to_view(updated)

            kb = connection.execute(
                "SELECT id FROM knowledge_bases WHERE class_id=? AND owner_teacher_id=? AND kind='class_copy'",
                (class_id, teacher.id),
            ).fetchone()
            if kb is None:
                raise BusinessError(status_code=409, code="CLASS_KNOWLEDGE_BASE_NOT_READY", message="请先从知识库管理导入课件")

            placeholders = ",".join("?" for _ in selected_ids)
            docs = connection.execute(
                f"""SELECT id, original_filename, parse_status, version
                    FROM knowledge_base_documents
                    WHERE knowledge_base_id=? AND id IN ({placeholders})
                    ORDER BY created_at, id""",
                (kb["id"], *selected_ids),
            ).fetchall()
            if len(docs) != len(selected_ids):
                raise BusinessError(status_code=404, code="PREPARATION_DOCUMENT_NOT_FOUND", message="文档不存在")
            if any(d["parse_status"] != "completed" for d in docs):
                raise BusinessError(status_code=409, code="PREPARATION_DOCUMENT_NOT_READY", message="只有完成解析的文档可以进入备课")

            settings = self._knowledge_base_service.ensure_settings(connection, kb["id"], now)
            segment_rule = self._segment_rule_label(settings)
            doc_by_id = {d["id"]: d for d in docs}
            ordered_docs = [doc_by_id[did] for did in selected_ids]

            self._clear_relationship_state(connection, session["id"])
            connection.executemany(
                "INSERT INTO preparation_session_documents(session_id,document_id,ordinal,document_version,created_at) VALUES(?,?,?,?,?)",
                [(session["id"], d["id"], i, d["version"], now) for i, d in enumerate(ordered_docs)],
            )
            block_rows = []
            for doc in ordered_docs:
                rows = connection.execute(
                    """SELECT id, document_id, document_version, content
                       FROM knowledge_base_chunks
                       WHERE knowledge_base_id=? AND document_id=? AND index_status='ready'
                       ORDER BY ordinal""",
                    (kb["id"], doc["id"]),
                ).fetchall()
                if not rows:
                    raise BusinessError(status_code=409, code="PREPARATION_DOCUMENT_SEGMENTS_NOT_READY", message="文档尚未索引")
                block_rows.extend(
                    (r["id"], r["document_id"], r["document_version"], segment_rule, r["content"])
                    for r in rows
                )
            connection.executemany(
                "INSERT INTO preparation_session_segments(session_id,ordinal,document_id,chunk_id,document_version,block_type,content,created_at) VALUES(?,?,?,?,?,?,?,?)",
                [(session["id"], i, did, cid, dv, bt, c, now) for i, (cid, did, dv, bt, c) in enumerate(block_rows)],
            )

            filenames = "、".join(d["original_filename"] for d in ordered_docs)
            connection.execute(
                """UPDATE preparation_sessions
                   SET original_filename=?, file_format='markdown', file_size_bytes=1,
                       upload_status='uploaded', parse_status='completed',
                       current_step='highlighting', storage_key=NULL,
                       parse_error_code=NULL, parse_started_at=NULL,
                       parse_completed_at=?, parsed_content_reference=?,
                       knowledge_base_id=?, updated_at=?
                   WHERE id=?""",
                (filenames, now, f"knowledge-base:{kb['id']}", kb["id"], now, session["id"]),
            )
            updated = self._records.find(connection, class_id)
        if updated is None:
            raise RuntimeError("选择知识库文档后备课会话缺失")
        return self._records.to_view(updated)

    @staticmethod
    def _clear_relationship_state(connection: sqlite3.Connection, session_id: str) -> None:
        for table in ("preparation_session_documents", "preparation_session_segments",
                      "preparation_highlights", "preparation_questions"):
            connection.execute(f"DELETE FROM {table} WHERE session_id = ?", (session_id,))
        connection.execute("UPDATE preparation_sessions SET published_at=NULL, published_content_ids_json='[]' WHERE id=?", (session_id,))

    # ── 段落查询 ──────────────────────────────────────────────

    def get_preparation_session_paragraphs(
        self, class_id: str, teacher: UserView,
    ) -> list[PreparationSessionParagraphView]:
        """读取已完成会话的有序段落。"""
        with self._database.connect() as connection:
            session = self._require_session(connection, class_id, teacher)
            if session["parse_status"] != ParseStatus.COMPLETED.value:
                return []
            rows = [
                dict(r) for r in connection.execute(
                    """SELECT p.ordinal, p.document_id, d.original_filename AS document_filename,
                              p.block_type, p.content
                       FROM preparation_session_segments p
                       LEFT JOIN knowledge_base_documents d ON d.id = p.document_id
                       WHERE p.session_id = ?
                       ORDER BY p.ordinal""",
                    (session["id"],),
                ).fetchall()
            ]
        return [
            PreparationSessionParagraphView(
                ordinal=r["ordinal"], document_id=r["document_id"],
                document_filename=r["document_filename"],
                block_type=r["block_type"], content=r["content"],
            ) for r in rows
        ]

    # ── 文件上传 ──────────────────────────────────────────────

    def replace_preparation_session_file(
        self, class_id: str, filename: str, content: bytes, teacher: UserView,
    ) -> PreparationSessionView:
        """原子替换受控原文件。"""
        file_format = validate_file_content(filename, content)
        now = self._now()
        self._upload_root.mkdir(parents=True, exist_ok=True)
        storage_key = generate_storage_key(filename)
        target = self._upload_root / storage_key
        target.write_bytes(content)
        try:
            with self._database.connect() as connection:
                row = self._require_session(connection, class_id, teacher)
                old_key = row["storage_key"]
                self._clear_relationship_state(connection, row["id"])
                connection.execute(
                    """UPDATE preparation_sessions SET original_filename=?, file_format=?,
                       file_size_bytes=?, storage_key=?, upload_status=?,
                       parse_status=?, current_step=?, parse_error_code=NULL,
                       parse_started_at=NULL, parse_completed_at=NULL,
                       parsed_content_reference=NULL, updated_at=?
                       WHERE id=?""",
                    (filename, file_format.value, len(content), storage_key,
                     UploadStatus.UPLOADED.value, ParseStatus.NOT_STARTED.value,
                     CurrentStep.UPLOAD.value, now, row["id"]),
                )
                updated = self._records.find(connection, class_id)
            if old_key:
                (self._upload_root / old_key).unlink(missing_ok=True)
            return self._records.to_view(updated)
        except Exception:
            target.unlink(missing_ok=True)
            raise

    # ── 解析 ──────────────────────────────────────────────────

    def start_preparation_session_parsing(self, class_id: str, teacher: UserView) -> PreparationSessionView:
        """持久化 parsing 状态后交给独立线程。"""
        now = self._now()
        session_id: str | None = None
        storage_key: str | None = None
        file_format: FileFormat | None = None
        with self._database.connect() as connection:
            row = self._require_session(connection, class_id, teacher)
            if not row["storage_key"]:
                raise BusinessError(status_code=404, code="PREPARATION_SESSION_NOT_FOUND", message="备课会话不存在")
            self._clear_relationship_state(connection, row["id"])
            connection.execute(
                """UPDATE preparation_sessions
                   SET parse_status=?, current_step=?, parse_error_code=NULL,
                       parse_started_at=?, parse_completed_at=NULL, updated_at=?
                   WHERE id=?""",
                (ParseStatus.PARSING.value, CurrentStep.PARSING.value, now, now, row["id"]),
            )
            session_id = row["id"]
            storage_key = row["storage_key"]
            file_format = FileFormat(row["file_format"])
            updated = self._records.find(connection, class_id)
        # 退出 with 块后再启动后台线程，确保连接已释放
        self._parsing_orchestrator.execute_parse_background(session_id, storage_key, file_format)
        return self._records.to_view(updated)

    # ── 教学重点 ──────────────────────────────────────────────

    def get_preparation_session_paragraphs_with_highlights(
        self, class_id: str, teacher: UserView,
    ) -> PreparationSessionParsingResultWithHighlightsView:
        """读取已完成会话的有序段落和教学重点。"""
        with self._database.connect() as connection:
            session = self._require_session(connection, class_id, teacher)
            sub_view = self._records.to_view(session)
            paragraphs, total = self._highlight_manager.get_paragraphs_with_highlights(connection, session)
            return PreparationSessionParsingResultWithHighlightsView(
                session=sub_view,
                paragraphs=paragraphs,
                total_highlights=total,
            )

    def add_highlight(
        self, class_id: str, request: AddHighlightRequest, teacher: UserView,
    ) -> HighlightView:
        """新增教学重点。"""
        with self._database.connect() as connection:
            session = self._require_session(connection, class_id, teacher)
            return self._highlight_manager.add_highlight(connection, session, request)

    def remove_highlight(
        self, class_id: str, request: RemoveHighlightRequest, teacher: UserView,
    ) -> None:
        """取消教学重点。"""
        with self._database.connect() as connection:
            session = self._require_session(connection, class_id, teacher)
            self._highlight_manager.remove_highlight(connection, session, request.highlight_id)

    # ── 题目管理 ──────────────────────────────────────────────

    def list_questions(self, class_id: str, teacher: UserView) -> QuestionListView:
        """获取题目列表。"""
        with self._database.connect() as connection:
            session = self._require_session(connection, class_id, teacher)
            return self._question_manager.list_questions(connection, session)

    def generate_candidate_questions(
        self, class_id: str, teacher: UserView,
    ) -> CandidateQuestionGenerationView:
        """根据教学重点生成候选题。"""
        with self._database.connect() as connection:
            session = self._require_session(connection, class_id, teacher)
            paragraph_rows = [
                dict(r) for r in connection.execute(
                    """SELECT p.ordinal, p.document_id, d.original_filename AS document_filename,
                              p.block_type, p.content
                       FROM preparation_session_segments p
                       LEFT JOIN knowledge_base_documents d ON d.id = p.document_id
                       WHERE p.session_id = ?
                       ORDER BY p.ordinal""",
                    (session["id"],),
                ).fetchall()
            ]
            return self._question_manager.generate_candidate_questions(
                connection, session, paragraph_rows, teacher.id,
            )

    def create_question(
        self, class_id: str, request: CreateQuestionRequest, teacher: UserView,
    ) -> QuestionView:
        """创建手工题。"""
        with self._database.connect() as connection:
            session = self._require_session(connection, class_id, teacher)
            return self._question_manager.create_question(connection, session, request)

    def update_question(
        self, class_id: str, question_id: str, request: UpdateQuestionRequest, teacher: UserView,
    ) -> QuestionView:
        """更新题目。"""
        with self._database.connect() as connection:
            session = self._require_session(connection, class_id, teacher)
            return self._question_manager.update_question(connection, session, question_id, request)

    def confirm_candidate_question(
        self, class_id: str, request: ConfirmCandidateQuestionRequest, teacher: UserView,
    ) -> QuestionView:
        """确认候选题。"""
        with self._database.connect() as connection:
            session = self._require_session(connection, class_id, teacher)
            return self._question_manager.confirm_candidate_question(connection, session, request)

    def delete_question(
        self, class_id: str, request: DeleteQuestionRequest, teacher: UserView,
    ) -> None:
        """删除题目。"""
        with self._database.connect() as connection:
            session = self._require_session(connection, class_id, teacher)
            self._question_manager.delete_question(connection, session, request)
