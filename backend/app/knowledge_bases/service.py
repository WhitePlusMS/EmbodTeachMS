"""课件知识库管理 Facade 模块。

作为知识库管理的窄接口 Facade，组合内部子模块：
- DocumentStore：文档 CRUD、文件存储、解析状态
- KnowledgeBaseSearcher：FTS5 和向量检索
- KnowledgeBasePublisher：复制、导入、发布

外部代码只通过此 Facade 或 __init__ 暴露的 exports 与知识库模块交互。
"""
from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from collections.abc import Callable
from pathlib import Path

from app.auth.models import UserRole, UserView
from app.common.errors import BusinessError
from app.database import Database
from app.document_parsing import MarkdownParser, ParsingError
from app.document_parsing.models import NormalizedDocument, ParsedBlock
from app.knowledge_bases.chunking import ChunkingConfig, chunk_document
from app.knowledge_bases.document_store import KnowledgeBaseDocumentStore
from app.knowledge_bases.models import (
    CopyKnowledgeBaseRequest,
    CreateKnowledgeBaseRequest,
    ImportKnowledgeBaseDocumentsRequest,
    KnowledgeBaseBuildView,
    KnowledgeBaseImportView,
    KnowledgeBaseIndexStatusView,
    KnowledgeBaseKind,
    KnowledgeBaseListView,
    KnowledgeBasePublicationView,
    KnowledgeBaseSearchView,
    KnowledgeBaseSegmentListView,
    KnowledgeBaseSegmentPreviewRequest,
    KnowledgeBaseSegmentPreviewView,
    KnowledgeBaseSegmentRebuildView,
    KnowledgeBaseSegmentView,
    KnowledgeBaseSettingsView,
    KnowledgeBaseStatus,
    KnowledgeBaseView,
    KnowledgeBaseWorkspaceView,
    KnowledgeBaseDocumentView,
    KnowledgeBaseDocumentListView,
    KnowledgeBaseRetrievalTestRequest,
    UpdateKnowledgeBaseDocumentRequest,
    UpdateKnowledgeBaseRequest,
    UpdateKnowledgeBaseSettingsRequest,
    DEFAULT_ADVANCED_SEPARATORS,
)
from app.knowledge_bases.publisher import KnowledgeBasePublisher
from app.knowledge_bases.searcher import KnowledgeBaseSearcher


logger = logging.getLogger("course_agent.knowledge_bases")


class KnowledgeBaseService:
    """知识库管理窄 Facade——组合内部 DocumentStore / Searcher / Publisher。

    职责仅限于：知识库元数据 CRUD → 委托给正确子模块 · 分段预览/重建
    所有检索逻辑委托给 KnowledgeBaseSearcher
    所有文档 CRUD 委托给 DocumentStore
    所有复制/导入/发布委托给 KnowledgeBasePublisher
    """

    def __init__(self, database: Database, now_provider: Callable[[], int]) -> None:
        self._database = database
        self._now = now_provider
        self._database_path = database.path

        # 内部模块
        self._store = KnowledgeBaseDocumentStore(
            database.connect, now_provider, database.path,
        )
        self._searcher = KnowledgeBaseSearcher(database.connect)
        self._publisher = KnowledgeBasePublisher(
            database.connect, now_provider, self._store, self._searcher, database.path,
        )

    # ── 知识库 CRUD ───────────────────────────────────────────────

    @staticmethod
    def _resource_not_found(message: str = "知识库不存在") -> BusinessError:
        return BusinessError(status_code=404, code="RESOURCE_NOT_FOUND", message=message)

    def _require_owned_knowledge_base(
        self,
        connection: sqlite3.Connection,
        knowledge_base_id: str,
        teacher: UserView,
    ) -> sqlite3.Row:
        row = connection.execute(
            """SELECT id, owner_teacher_id, class_id, source_knowledge_base_id,
                      kind, name, description, status, source_version,
                      archived_at, created_at, updated_at
               FROM knowledge_bases
               WHERE id = ? AND owner_teacher_id = ?""",
            (knowledge_base_id, teacher.id),
        ).fetchone()
        if row is None:
            raise self._resource_not_found()
        return row

    @staticmethod
    def _to_view(row: sqlite3.Row, document_count: int) -> KnowledgeBaseView:
        return KnowledgeBaseView(
            id=row["id"], owner_teacher_id=row["owner_teacher_id"],
            class_id=row["class_id"], source_knowledge_base_id=row["source_knowledge_base_id"],
            kind=KnowledgeBaseKind(row["kind"]), name=row["name"],
            description=row["description"], status=KnowledgeBaseStatus(row["status"]),
            source_version=row["source_version"], document_count=document_count,
            archived_at=row["archived_at"], created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _view_for_row(self, connection: sqlite3.Connection, row: sqlite3.Row) -> KnowledgeBaseView:
        document_count = connection.execute(
            "SELECT COUNT(*) FROM knowledge_base_documents WHERE knowledge_base_id = ?",
            (row["id"],),
        ).fetchone()[0]
        return self._to_view(row, document_count)

    @staticmethod
    def _settings_view(row: sqlite3.Row) -> KnowledgeBaseSettingsView:
        return KnowledgeBaseSettingsView(
            knowledge_base_id=row["knowledge_base_id"], mode=row["mode"],
            max_characters=row["max_characters"], overlap_characters=row["overlap_characters"],
            separators=json.loads(row["separators_json"]),
            cleaning_rules=json.loads(row["cleaning_rules_json"]),
            index_version=row["index_version"], updated_at=row["updated_at"],
        )

    def _ensure_settings(self, connection: sqlite3.Connection, knowledge_base_id: str, now: int) -> sqlite3.Row:
        row = connection.execute(
            """SELECT id AS knowledge_base_id, segment_mode AS mode,
                      segment_max_characters AS max_characters,
                      segment_overlap_characters AS overlap_characters,
                      segment_separators_json AS separators_json,
                      segment_cleaning_rules_json AS cleaning_rules_json,
                      segment_index_version AS index_version,
                      segment_settings_updated_at AS updated_at
               FROM knowledge_bases WHERE id = ?""",
            (knowledge_base_id,),
        ).fetchone()
        if row is not None and all(
            row[col] is not None
            for col in ("mode", "max_characters", "overlap_characters",
                        "separators_json", "cleaning_rules_json",
                        "index_version", "updated_at")
        ):
            return row
        connection.execute(
            """UPDATE knowledge_bases
               SET segment_mode = 'simple', segment_max_characters = 2400,
                   segment_overlap_characters = 2400 / 10,
                   segment_separators_json = ?, segment_cleaning_rules_json = '[]',
                   segment_index_version = 1, segment_settings_updated_at = ?
               WHERE id = ?""",
            (json.dumps(DEFAULT_ADVANCED_SEPARATORS, ensure_ascii=False), now, knowledge_base_id),
        )
        return connection.execute(
            """SELECT id AS knowledge_base_id, segment_mode AS mode,
                      segment_max_characters AS max_characters,
                      segment_overlap_characters AS overlap_characters,
                      segment_separators_json AS separators_json,
                      segment_cleaning_rules_json AS cleaning_rules_json,
                      segment_index_version AS index_version,
                      segment_settings_updated_at AS updated_at
               FROM knowledge_bases WHERE id = ?""",
            (knowledge_base_id,),
        ).fetchone()

    def ensure_settings(self, connection: sqlite3.Connection, knowledge_base_id: str, now: int) -> sqlite3.Row:
        """为其他知识库协作者提供同一套设置初始化 seam。"""
        return self._ensure_settings(connection, knowledge_base_id, now)

    @staticmethod
    def _chunking_config(request: UpdateKnowledgeBaseSettingsRequest) -> ChunkingConfig:
        if request.overlap_characters >= request.max_characters:
            raise BusinessError(
                status_code=400, code="SEGMENT_OVERLAP_INVALID",
                message="分段重叠长度必须小于最大长度",
            )
        return ChunkingConfig(
            max_characters=request.max_characters,
            overlap_characters=request.overlap_characters,
            mode=request.mode,
            separators=tuple(request.separators),
            cleaning_rules=tuple(request.cleaning_rules),
            strategy_version=f"{request.mode}-v1",
        )

    # ── 知识库 CRUD ───────────────────────────────────────────────

    def create(self, request: CreateKnowledgeBaseRequest, teacher: UserView) -> KnowledgeBaseView:
        now = self._now()
        knowledge_base_id = str(uuid.uuid4())
        with self._database.connect() as connection:
            name_conflict = connection.execute(
                "SELECT 1 FROM knowledge_bases WHERE owner_teacher_id = ? AND kind = ? AND name = ?",
                (teacher.id, KnowledgeBaseKind.REUSABLE.value, request.name),
            ).fetchone()
            if name_conflict is not None:
                raise BusinessError(status_code=409, code="KNOWLEDGE_BASE_NAME_CONFLICT", message="知识库名称已存在")
            connection.execute(
                """INSERT INTO knowledge_bases (
                       id, owner_teacher_id, class_id, source_knowledge_base_id,
                       kind, name, description, status, source_version,
                       archived_at, created_at, updated_at)
                   VALUES (?, ?, NULL, NULL, ?, ?, ?, ?, 1, NULL, ?, ?)""",
                (knowledge_base_id, teacher.id, KnowledgeBaseKind.REUSABLE.value,
                 request.name, request.description, KnowledgeBaseStatus.DRAFT.value, now, now),
            )
            row = self._require_owned_knowledge_base(connection, knowledge_base_id, teacher)
            view = self._view_for_row(connection, row)
        logger.info("knowledge_base_created knowledge_base_id=%s teacher_id=%s", knowledge_base_id, teacher.id)
        return view

    def list_for_teacher(self, teacher: UserView) -> KnowledgeBaseListView:
        with self._database.connect() as connection:
            rows = connection.execute(
                """SELECT kb.id, kb.owner_teacher_id, kb.class_id,
                          kb.source_knowledge_base_id, kb.kind, kb.name,
                          kb.description, kb.status, kb.source_version,
                          kb.archived_at, kb.created_at, kb.updated_at,
                          COUNT(kbd.id) AS document_count
                   FROM knowledge_bases kb
                   LEFT JOIN knowledge_base_documents kbd ON kbd.knowledge_base_id = kb.id
                   WHERE kb.owner_teacher_id = ?
                   GROUP BY kb.id
                   ORDER BY kb.updated_at DESC, kb.id DESC""",
                (teacher.id,),
            ).fetchall()
        return KnowledgeBaseListView(
            items=[self._to_view(row, row["document_count"]) for row in rows]
        )

    def get(self, knowledge_base_id: str, teacher: UserView) -> KnowledgeBaseView:
        with self._database.connect() as connection:
            row = self._require_owned_knowledge_base(connection, knowledge_base_id, teacher)
            return self._view_for_row(connection, row)

    def update(self, knowledge_base_id: str, request: UpdateKnowledgeBaseRequest, teacher: UserView) -> KnowledgeBaseView:
        if request.name is None and request.description is None:
            raise BusinessError(status_code=400, code="KNOWLEDGE_BASE_UPDATE_EMPTY", message="至少提供一个需要更新的字段")
        now = self._now()
        with self._database.connect() as connection:
            row = self._require_owned_knowledge_base(connection, knowledge_base_id, teacher)
            next_name = request.name or row["name"]
            if request.name is not None:
                conflict = connection.execute(
                    "SELECT 1 FROM knowledge_bases WHERE owner_teacher_id = ? AND kind = ? AND name = ? AND id != ?",
                    (teacher.id, KnowledgeBaseKind.REUSABLE.value, next_name, knowledge_base_id),
                ).fetchone()
                if conflict is not None and row["kind"] == KnowledgeBaseKind.REUSABLE:
                    raise BusinessError(status_code=409, code="KNOWLEDGE_BASE_NAME_CONFLICT", message="知识库名称已存在")
            next_description = request.description if request.description is not None else row["description"]
            connection.execute(
                "UPDATE knowledge_bases SET name = ?, description = ?, updated_at = ? WHERE id = ? AND owner_teacher_id = ?",
                (next_name, next_description, now, knowledge_base_id, teacher.id),
            )
            updated_row = self._require_owned_knowledge_base(connection, knowledge_base_id, teacher)
            view = self._view_for_row(connection, updated_row)
        logger.info("knowledge_base_updated knowledge_base_id=%s teacher_id=%s", knowledge_base_id, teacher.id)
        return view

    def archive(self, knowledge_base_id: str, teacher: UserView) -> KnowledgeBaseView:
        now = self._now()
        with self._database.connect() as connection:
            self._require_owned_knowledge_base(connection, knowledge_base_id, teacher)
            connection.execute(
                "UPDATE knowledge_bases SET status = ?, archived_at = ?, updated_at = ? WHERE id = ? AND owner_teacher_id = ?",
                (KnowledgeBaseStatus.ARCHIVED.value, now, now, knowledge_base_id, teacher.id),
            )
            row = self._require_owned_knowledge_base(connection, knowledge_base_id, teacher)
            view = self._view_for_row(connection, row)
        logger.info("knowledge_base_archived knowledge_base_id=%s teacher_id=%s", knowledge_base_id, teacher.id)
        return view

    def delete(self, knowledge_base_id: str, teacher: UserView) -> None:
        with self._database.connect() as connection:
            self._require_owned_knowledge_base(connection, knowledge_base_id, teacher)
            copy_count = connection.execute(
                "SELECT COUNT(*) FROM knowledge_bases WHERE source_knowledge_base_id = ?",
                (knowledge_base_id,),
            ).fetchone()[0]
            if copy_count:
                raise BusinessError(status_code=409, code="KNOWLEDGE_BASE_HAS_COPIES", message="知识库已有教学班副本，不能删除来源知识库")
            connection.execute(
                "DELETE FROM knowledge_bases WHERE id = ? AND owner_teacher_id = ?",
                (knowledge_base_id, teacher.id),
            )
        logger.info("knowledge_base_deleted knowledge_base_id=%s teacher_id=%s", knowledge_base_id, teacher.id)

    # ── 文档操作（委托给 DocumentStore）───────────────────────────

    def _authorize(
        self, knowledge_base_id: str, teacher: UserView,
    ) -> None:
        """鉴权知识库归属，消除文档 CRUD 方法中的重复样板。"""
        with self._database.connect() as connection:
            self._require_owned_knowledge_base(connection, knowledge_base_id, teacher)

    def list_documents(self, knowledge_base_id: str, teacher: UserView) -> KnowledgeBaseDocumentListView:
        self._authorize(knowledge_base_id, teacher)
        return self._store.list_documents(knowledge_base_id)

    def get_document(self, knowledge_base_id: str, document_id: str, teacher: UserView) -> KnowledgeBaseDocumentView:
        self._authorize(knowledge_base_id, teacher)
        return self._store.get_document(document_id, knowledge_base_id)

    def get_document_source_path(self, knowledge_base_id: str, document_id: str, teacher: UserView) -> Path:
        self._authorize(knowledge_base_id, teacher)
        return self._store.get_document_source_path(document_id, knowledge_base_id)

    def save_uploaded_document(self, knowledge_base_id: str, filename: str, content: bytes, teacher: UserView) -> KnowledgeBaseDocumentView:
        self._authorize(knowledge_base_id, teacher)
        return self._store.save_uploaded_document(knowledge_base_id, filename, content)

    def update_document(self, knowledge_base_id: str, document_id: str, request: UpdateKnowledgeBaseDocumentRequest, teacher: UserView) -> KnowledgeBaseDocumentView:
        self._authorize(knowledge_base_id, teacher)
        return self._store.update_document(knowledge_base_id, document_id, request)

    def replace_document_source(self, knowledge_base_id: str, document_id: str, filename: str, content: bytes, teacher: UserView) -> KnowledgeBaseDocumentView:
        self._authorize(knowledge_base_id, teacher)
        return self._store.replace_document_source(knowledge_base_id, document_id, filename, content)

    def delete_document(self, knowledge_base_id: str, document_id: str, teacher: UserView) -> None:
        self._authorize(knowledge_base_id, teacher)
        self._store.delete_document(knowledge_base_id, document_id)

    def mark_document_parsing(self, document_id: str, teacher: UserView) -> int:
        # 确认拥有的校验在 document_store 里不重复做，由 router 确保前置验证
        return self._store.mark_document_parsing(document_id)

    def save_document(self, knowledge_base_id: str, filename: str, file_format: str, normalized_document: NormalizedDocument, teacher: UserView) -> KnowledgeBaseDocumentView:
        with self._database.connect() as connection:
            self._require_owned_knowledge_base(connection, knowledge_base_id, teacher)
            now = self._now()
            document_id = str(uuid.uuid4())
            title = filename.rsplit(".", 1)[0][:200] or filename
            connection.execute(
                """INSERT INTO knowledge_base_documents
                   (id, knowledge_base_id, source_document_id, title, original_filename,
                    file_format, parse_status, parser_name, parser_version, content_hash,
                    error_code, error_message, created_at, updated_at)
                   VALUES (?, ?, NULL, ?, ?, 'markdown', 'completed', ?, ?, ?, NULL, NULL, ?, ?)""",
                (document_id, knowledge_base_id, title, filename,
                 normalized_document.parser_name, normalized_document.parser_version,
                 normalized_document.content_sha256, now, now),
            )
            self._store.save_document_content(connection, document_id, normalized_document.markdown)
            self._insert_blocks(connection, document_id, normalized_document.blocks)
            chunks = chunk_document(normalized_document, knowledge_base_id=knowledge_base_id,
                                     document_id=document_id, document_version=1)
            self._insert_chunks(connection, chunks, knowledge_base_id)
            row = connection.execute(
                """SELECT id, knowledge_base_id, source_document_id, title,
                          original_filename, file_format, parse_status, error_code,
                          error_message, parser_name, parser_version, created_at, updated_at
                   FROM knowledge_base_documents WHERE id = ?""",
                (document_id,),
            ).fetchone()
        return KnowledgeBaseDocumentView(**dict(row))

    def complete_uploaded_document(
        self, document_id: str, normalized_document: NormalizedDocument, teacher: UserView,
        *, expected_version: int, build_index: bool = True,
    ) -> KnowledgeBaseDocumentView:
        return self._store.complete_uploaded_document(
            document_id, normalized_document, expected_version=expected_version, build_index=build_index,
        )

    def mark_document_failed(self, document_id: str, error_code: str, error_message: str, teacher: UserView,
                             *, expected_version: int | None = None) -> KnowledgeBaseDocumentView:
        return self._store.mark_document_failed(document_id, error_code, error_message, expected_version=expected_version)

    def save_failed_document(self, knowledge_base_id: str, filename: str, file_format: str, content: bytes, error_code: str, teacher: UserView) -> KnowledgeBaseDocumentView:
        with self._database.connect() as connection:
            self._require_owned_knowledge_base(connection, knowledge_base_id, teacher)
        return self._store.save_failed_document(knowledge_base_id, filename, file_format, content, error_code)

    def get_failed_document_source(self, document_id: str, teacher: UserView) -> tuple[str, str, str, Path]:
        return self._store.get_failed_document_source(document_id)

    def list_build_documents(self, knowledge_base_id: str, teacher: UserView) -> list[tuple[str, Path]]:
        with self._database.connect() as connection:
            self._require_owned_knowledge_base(connection, knowledge_base_id, teacher)
        return self._store.list_build_documents(knowledge_base_id)

    # ── 设置 ──────────────────────────────────────────────────────

    def get_settings(self, knowledge_base_id: str, teacher: UserView) -> KnowledgeBaseSettingsView:
        with self._database.connect() as connection:
            self._require_owned_knowledge_base(connection, knowledge_base_id, teacher)
            row = self._ensure_settings(connection, knowledge_base_id, self._now())
        return self._settings_view(row)

    def update_settings(
        self, knowledge_base_id: str, request: UpdateKnowledgeBaseSettingsRequest, teacher: UserView,
    ) -> KnowledgeBaseSettingsView:
        self._chunking_config(request)
        now = self._now()
        with self._database.connect() as connection:
            self._require_owned_knowledge_base(connection, knowledge_base_id, teacher)
            current = self._ensure_settings(connection, knowledge_base_id, now)
            document_rows = connection.execute(
                "SELECT id FROM knowledge_base_documents WHERE knowledge_base_id = ?",
                (knowledge_base_id,),
            ).fetchall()
            for document_row in document_rows:
                self._store.invalidate_document_chunks(connection, document_row["id"])
            connection.execute(
                """UPDATE knowledge_bases
                   SET segment_mode = ?, segment_max_characters = ?,
                       segment_overlap_characters = ?, segment_separators_json = ?,
                       segment_cleaning_rules_json = ?, segment_index_version = segment_index_version + 1,
                       segment_settings_updated_at = ?
                   WHERE id = ?""",
                (request.mode, request.max_characters, request.overlap_characters,
                 json.dumps(request.separators, ensure_ascii=False),
                 json.dumps(request.cleaning_rules, ensure_ascii=False), now, knowledge_base_id),
            )
            updated = connection.execute(
                """SELECT id AS knowledge_base_id, segment_mode AS mode,
                          segment_max_characters AS max_characters,
                          segment_overlap_characters AS overlap_characters,
                          segment_separators_json AS separators_json,
                          segment_cleaning_rules_json AS cleaning_rules_json,
                          segment_index_version AS index_version,
                          segment_settings_updated_at AS updated_at
                   FROM knowledge_bases WHERE id = ?""",
                (knowledge_base_id,),
            ).fetchone()
        logger.info(
            "knowledge_base_segment_settings_updated knowledge_base_id=%s previous_index_version=%s",
            knowledge_base_id, current["index_version"],
        )
        return self._settings_view(updated)

    # ── 分段预览/重建 ─────────────────────────────────────────────

    def _load_segment_source(
        self, connection: sqlite3.Connection, knowledge_base_id: str, document_id: str, teacher: UserView,
    ) -> tuple[sqlite3.Row, NormalizedDocument]:
        self._require_owned_knowledge_base(connection, knowledge_base_id, teacher)
        return self._store.load_segment_source(connection, knowledge_base_id, document_id)

    @staticmethod
    def _preview_segment(chunk, document: sqlite3.Row, index_status: str = "pending") -> KnowledgeBaseSegmentView:
        return KnowledgeBaseSegmentView(
            id=chunk.id, document_id=chunk.document_id,
            document_filename=document["original_filename"],
            document_version=chunk.document_version, ordinal=chunk.ordinal,
            content=chunk.content, title_path=list(chunk.title_path),
            page_start=chunk.page_start, page_end=chunk.page_end,
            source_position=chunk.source_position,
            index_status=index_status, chunk_strategy_version=chunk.chunk_strategy_version,
        )

    def preview_segments(
        self, knowledge_base_id: str, request: KnowledgeBaseSegmentPreviewRequest, teacher: UserView,
    ) -> KnowledgeBaseSegmentPreviewView:
        config = self._chunking_config(request)
        with self._database.connect() as connection:
            document, normalized = self._load_segment_source(connection, knowledge_base_id, request.document_id, teacher)
        chunks = chunk_document(normalized, knowledge_base_id=knowledge_base_id,
                                 document_id=request.document_id, document_version=document["version"], config=config)
        return KnowledgeBaseSegmentPreviewView(
            document_id=request.document_id, document_version=document["version"],
            mode=request.mode,
            segments=[self._preview_segment(chunk, document) for chunk in chunks],
            requires_rebuild=True,
        )

    def rebuild_segments(
        self, knowledge_base_id: str, request: KnowledgeBaseSegmentPreviewRequest, teacher: UserView,
    ) -> KnowledgeBaseSegmentRebuildView:
        config = self._chunking_config(request)
        now = self._now()
        with self._database.connect() as connection:
            document, normalized = self._load_segment_source(connection, knowledge_base_id, request.document_id, teacher)
            chunks = chunk_document(normalized, knowledge_base_id=knowledge_base_id,
                                     document_id=request.document_id,
                                     document_version=document["version"], config=config)
            self._store.invalidate_document_chunks(connection, request.document_id)
            self._insert_chunks(connection, chunks, knowledge_base_id)
            current_settings = self._ensure_settings(connection, knowledge_base_id, now)
            connection.execute(
                """UPDATE knowledge_bases
                   SET segment_mode = ?, segment_max_characters = ?,
                       segment_overlap_characters = ?, segment_separators_json = ?,
                       segment_cleaning_rules_json = ?, segment_index_version = segment_index_version + 1,
                       segment_settings_updated_at = ?
                   WHERE id = ?""",
                (request.mode, request.max_characters, request.overlap_characters,
                 json.dumps(request.separators, ensure_ascii=False),
                 json.dumps(request.cleaning_rules, ensure_ascii=False), now, knowledge_base_id),
            )
            settings = connection.execute(
                """SELECT id AS knowledge_base_id, segment_mode AS mode,
                          segment_max_characters AS max_characters,
                          segment_overlap_characters AS overlap_characters,
                          segment_separators_json AS separators_json,
                          segment_cleaning_rules_json AS cleaning_rules_json,
                          segment_index_version AS index_version,
                          segment_settings_updated_at AS updated_at
                   FROM knowledge_bases WHERE id = ?""",
                (knowledge_base_id,),
            ).fetchone()
        logger.info(
            "knowledge_base_segments_rebuilt knowledge_base_id=%s document_id=%s chunk_count=%s",
            knowledge_base_id, request.document_id, len(chunks),
        )
        return KnowledgeBaseSegmentRebuildView(
            knowledge_base_id=knowledge_base_id, document_id=request.document_id,
            chunk_count=len(chunks), index_status="ready",
            settings=self._settings_view(settings),
        )

    def list_segments(self, knowledge_base_id: str, teacher: UserView) -> KnowledgeBaseSegmentListView:
        with self._database.connect() as connection:
            self._require_owned_knowledge_base(connection, knowledge_base_id, teacher)
            rows = connection.execute(
                """SELECT c.id, c.document_id, d.original_filename, c.document_version,
                          c.ordinal, c.content, c.title_path_json, c.page_start, c.page_end,
                          c.source_position, c.index_status, c.chunk_strategy_version
                   FROM knowledge_base_chunks c
                   JOIN knowledge_base_documents d ON d.id = c.document_id
                   WHERE c.knowledge_base_id = ? AND d.parse_status = 'completed'
                   ORDER BY d.updated_at DESC, d.id, c.ordinal""",
                (knowledge_base_id,),
            ).fetchall()
        return KnowledgeBaseSegmentListView(
            items=[
                KnowledgeBaseSegmentView(
                    id=row["id"], document_id=row["document_id"],
                    document_filename=row["original_filename"],
                    document_version=row["document_version"], ordinal=row["ordinal"],
                    content=row["content"], title_path=json.loads(row["title_path_json"]),
                    page_start=row["page_start"], page_end=row["page_end"],
                    source_position=row["source_position"], index_status=row["index_status"],
                    chunk_strategy_version=row["chunk_strategy_version"],
                )
                for row in rows
            ]
        )

    # ── 检索（委托给 Searcher）───────────────────────────────────

    def search_for_knowledge_base(
        self, knowledge_base_id: str, query: str, limit: int, teacher: UserView,
    ) -> KnowledgeBaseSearchView:
        with self._database.connect() as connection:
            self._require_owned_knowledge_base(connection, knowledge_base_id, teacher)
        return self._searcher.search_for_knowledge_base(knowledge_base_id, query, limit)

    def retrieval_test(
        self, knowledge_base_id: str, request: KnowledgeBaseRetrievalTestRequest, teacher: UserView,
    ) -> KnowledgeBaseSearchView:
        with self._database.connect() as connection:
            self._require_owned_knowledge_base(connection, knowledge_base_id, teacher)
        return self._searcher.retrieval_test(knowledge_base_id, request)

    def search_for_class(
        self, class_id: str, query: str, limit: int, teacher: UserView,
    ) -> KnowledgeBaseSearchView:
        with self._database.connect() as connection:
            class_row = connection.execute(
                "SELECT id FROM teaching_classes WHERE id = ? AND owner_teacher_id = ?",
                (class_id, teacher.id),
            ).fetchone()
            if class_row is None:
                raise self._resource_not_found("教学班不存在")
            kb = connection.execute(
                "SELECT id FROM knowledge_bases WHERE class_id = ? AND owner_teacher_id = ? AND kind = 'class_copy'",
                (class_id, teacher.id),
            ).fetchone()
            if kb is None:
                return KnowledgeBaseSearchView(results=[], retrieval_mode="fts5", has_results=False)
        return self._searcher.search_for_knowledge_base(kb["id"], query, limit)

    def search_for_class_member(
        self, class_id: str, query: str, limit: int, user: UserView,
    ) -> KnowledgeBaseSearchView:
        with self._database.connect() as connection:
            if user.role is UserRole.TEACHER:
                authorized = connection.execute(
                    "SELECT 1 FROM teaching_classes WHERE id = ? AND owner_teacher_id = ?",
                    (class_id, user.id),
                ).fetchone()
            else:
                authorized = connection.execute(
                    "SELECT 1 FROM class_memberships WHERE class_id = ? AND learner_id = ?",
                    (class_id, user.id),
                ).fetchone()
            if authorized is None:
                raise self._resource_not_found("教学班不存在或无权访问")
            knowledge_base = connection.execute(
                "SELECT id FROM knowledge_bases WHERE class_id = ? AND kind = 'class_copy'",
                (class_id,),
            ).fetchone()
            if knowledge_base is None:
                return KnowledgeBaseSearchView(results=[], retrieval_mode="fts5", has_results=False)
        return self._searcher.search_for_knowledge_base_as_user(knowledge_base["id"], query, limit)

    def search_for_knowledge_base_as_user(
        self, knowledge_base_id: str, query: str, limit: int,
    ) -> KnowledgeBaseSearchView:
        return self._searcher.search_for_knowledge_base_as_user(knowledge_base_id, query, limit)

    def get_index_status(self, knowledge_base_id: str, teacher: UserView) -> KnowledgeBaseIndexStatusView:
        with self._database.connect() as connection:
            self._require_owned_knowledge_base(connection, knowledge_base_id, teacher)
        return self._searcher.get_index_status(knowledge_base_id)

    def vectorize_knowledge_base(self, knowledge_base_id: str, teacher: UserView) -> str:
        with self._database.connect() as connection:
            self._require_owned_knowledge_base(connection, knowledge_base_id, teacher)
        return self._searcher.vectorize_knowledge_base(knowledge_base_id)

    # ── 发布/复制/导入（委托给 Publisher）─────────────────────────

    def copy_to_class(self, knowledge_base_id: str, request: CopyKnowledgeBaseRequest, teacher: UserView) -> KnowledgeBaseView:
        return self._publisher.copy_to_class(
            knowledge_base_id, request, teacher,
            self._require_owned_knowledge_base, self._view_for_row,
            self._ensure_settings, self._settings_view,
        )

    def import_documents(self, request: ImportKnowledgeBaseDocumentsRequest, teacher: UserView) -> KnowledgeBaseImportView:
        return self._publisher.import_documents(
            request, teacher,
            self._require_owned_knowledge_base, self._ensure_settings, self._view_for_row,
        )

    def publish_to_class(self, knowledge_base_id: str, teacher: UserView) -> KnowledgeBasePublicationView:
        with self._database.connect() as connection:
            knowledge_base = self._require_owned_knowledge_base(connection, knowledge_base_id, teacher)
            if knowledge_base["kind"] != KnowledgeBaseKind.CLASS_COPY.value or knowledge_base["class_id"] is None:
                raise BusinessError(
                    status_code=409, code="KNOWLEDGE_BASE_NOT_CLASS_COPY",
                    message="只有教学班知识库副本可以发布",
                )
        return self._publisher.publish_to_class(
            knowledge_base_id, knowledge_base["class_id"], knowledge_base["name"],
        )

    def build_result(
        self, knowledge_base_id: str, processed_count: int, succeeded_count: int,
        failed_count: int, embedding_status: str, teacher: UserView,
    ) -> KnowledgeBaseBuildView:
        with self._database.connect() as connection:
            self._require_owned_knowledge_base(connection, knowledge_base_id, teacher)
        return self._publisher.build_result(knowledge_base_id, processed_count, succeeded_count, failed_count, embedding_status)

    def get_for_class(self, class_id: str, teacher: UserView) -> KnowledgeBaseWorkspaceView | None:
        with self._database.connect() as connection:
            class_row = connection.execute(
                "SELECT id FROM teaching_classes WHERE id = ? AND owner_teacher_id = ?",
                (class_id, teacher.id),
            ).fetchone()
            if class_row is None:
                raise self._resource_not_found("教学班不存在")
        return self._publisher.get_for_class(class_id, teacher)

    # ── 文档解析辅助（从 router 下沉的业务逻辑）──────────────────

    def ensure_document_parsed(
        self, knowledge_base_id: str, document_id: str, teacher: UserView,
    ) -> None:
        """确保文档已解析可预览，按需触发单次解析。"""
        with self._database.connect() as connection:
            self._require_owned_knowledge_base(connection, knowledge_base_id, teacher)
        document = self._store.get_document(document_id, knowledge_base_id)
        if document.parse_status == "completed":
            return
        if document.parse_status == "parsing":
            raise BusinessError(status_code=409, code="DOCUMENT_PARSING", message="文档正在解析，请稍后刷新分段预览")
        if document.parse_status == "failed":
            raise BusinessError(status_code=409, code="DOCUMENT_PARSE_FAILED", message=document.error_message or "文档解析失败，请先重试")
        source_path = self._store.get_document_source_path(document_id, knowledge_base_id)
        if not source_path.is_file():
            self._store.mark_document_failed(document_id, "DOCUMENT_SOURCE_MISSING", "原始 Markdown 文件已不存在")
            raise BusinessError(status_code=409, code="DOCUMENT_SOURCE_MISSING", message="原始 Markdown 文件已不存在")
        expected_version = self._store.mark_document_parsing(document_id)
        try:
            result = MarkdownParser().parse_sync(source_path)
            if result.normalized_document is None or not result.normalized_document.markdown.strip():
                raise ParsingError(code="MARKDOWN_EMPTY", message="Markdown 文件没有可预览的内容")
            self._store.complete_uploaded_document(
                document_id, result.normalized_document, expected_version=expected_version, build_index=False,
            )
        except ParsingError as error:
            self._store.mark_document_failed(document_id, error.code, error.message, expected_version=expected_version)
            raise BusinessError(status_code=409, code=error.code, message=error.message) from error
        except OSError as error:
            self._store.mark_document_failed(document_id, "DOCUMENT_READ_FAILED", "Markdown 文件读取失败", expected_version=expected_version)
            raise BusinessError(status_code=409, code="DOCUMENT_READ_FAILED", message="Markdown 文件读取失败") from error
        except Exception:
            logger.exception("knowledge_base_on_demand_parse_failed document_id=%s", document_id)
            self._store.mark_document_failed(document_id, "KNOWLEDGE_BASE_PARSE_FAILED", "文档解析失败，请稍后重试", expected_version=expected_version)
            raise BusinessError(status_code=409, code="KNOWLEDGE_BASE_PARSE_FAILED", message="文档解析失败，请稍后重试")

    def import_documents_and_parse(
        self, request: ImportKnowledgeBaseDocumentsRequest, teacher: UserView,
    ) -> KnowledgeBaseImportView:
        """导入文档并在服务层完成全部解析和索引，出错时自动回滚已导入文档。"""
        imported = self._publisher.import_documents(
            request, teacher, self._require_owned_knowledge_base, self._ensure_settings, self._view_for_row,
        )
        target_id = imported.target_knowledge_base.id
        source_paths = dict(self._store.list_build_documents(target_id))
        parser = MarkdownParser()
        parse_versions: dict[str, int] = {}

        try:
            for document in imported.imported_documents:
                source_path = source_paths.get(document.id)
                if source_path is None:
                    raise BusinessError(status_code=409, code="DOCUMENT_SOURCE_MISSING", message="导入文档原始文件不存在")
                parse_versions[document.id] = self._store.mark_document_parsing(document.id)
                result = parser.parse_sync(source_path)
                if result.normalized_document is None or not result.normalized_document.markdown.strip():
                    raise ParsingError(code="MARKDOWN_EMPTY", message="Markdown 文件没有可构建的内容")
                self._store.complete_uploaded_document(
                    document.id, result.normalized_document, expected_version=parse_versions[document.id],
                )
        except (BusinessError, ParsingError) as error:
            for document in imported.imported_documents:
                self._store.delete_document(target_id, document.id)
            if isinstance(error, ParsingError):
                raise BusinessError(status_code=409, code=error.code, message=f"导入解析失败：{error.message}") from error
            raise
        except OSError:
            for document in imported.imported_documents:
                self._store.delete_document(target_id, document.id)
            raise BusinessError(status_code=409, code="DOCUMENT_READ_FAILED", message="导入文档读取失败")

        refreshed = self._store.list_documents(target_id)
        imported_ids = {d.id for d in imported.imported_documents}
        return KnowledgeBaseImportView(
            target_knowledge_base=imported.target_knowledge_base,
            imported_documents=[d for d in refreshed.items if d.id in imported_ids],
            skipped_document_ids=imported.skipped_document_ids,
        )

    # ── 内部帮助方法 ──────────────────────────────────────────────

    @staticmethod
    def _insert_blocks(connection: sqlite3.Connection, document_id: str, blocks: tuple[ParsedBlock, ...]) -> None:
        for block in blocks:
            source = block.source
            connection.execute(
                """INSERT INTO knowledge_base_blocks
                   (id, document_id, ordinal, block_type, title_path_json, content,
                    page_number, source_position, line_start, line_end)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (str(uuid.uuid4()), document_id, block.order, block.block_type,
                 json.dumps(list(block.title_path), ensure_ascii=False), block.content,
                 source.page_number if source else None, source.label if source else None,
                 source.line_start if source else None, source.line_end if source else None),
            )

    @staticmethod
    def _insert_chunks(connection: sqlite3.Connection, chunks, knowledge_base_id: str) -> None:
        from app.knowledge_bases.chunking import KnowledgeChunk
        for chunk in chunks:
            connection.execute(
                """INSERT INTO knowledge_base_chunks
                   (id, knowledge_base_id, document_id, document_version, ordinal,
                    content, title_path_json, page_start, page_end, source_position,
                    chunk_strategy_version, index_status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ready')""",
                (chunk.id, chunk.knowledge_base_id, chunk.document_id,
                 chunk.document_version, chunk.ordinal, chunk.content,
                 json.dumps(list(chunk.title_path), ensure_ascii=False),
                 chunk.page_start, chunk.page_end, chunk.source_position,
                 chunk.chunk_strategy_version),
            )
            connection.execute(
                """INSERT INTO knowledge_base_chunks_fts
                   (chunk_id, knowledge_base_id, content, title_path, source_position)
                   VALUES (?, ?, ?, ?, ?)""",
                (chunk.id, knowledge_base_id, chunk.content,
                 " / ".join(chunk.title_path), chunk.source_position or ""),
            )
