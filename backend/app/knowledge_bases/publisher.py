"""知识库发布、复制和导入模块。

从 KnowledgeBaseService 提取的独立模块，负责知识库复制到教学班、
按文档导入和课程内容快照发布。
"""
from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from collections.abc import Callable
from pathlib import Path

from app.auth.models import UserView
from app.common.errors import BusinessError
from app.knowledge_bases.models import (
    CopyKnowledgeBaseRequest,
    ImportKnowledgeBaseDocumentsRequest,
    KnowledgeBaseImportView,
    KnowledgeBaseKind,
    KnowledgeBaseStatus,
    KnowledgeBaseView,
    KnowledgeBasePublicationView,
    KnowledgeBaseWorkspaceView,
    KnowledgeBaseBuildView,
    KnowledgeBaseSettingsView,
    KnowledgeBaseDocumentView,
)
from app.knowledge_bases.chunking import ChunkingConfig


logger = logging.getLogger("course_agent.knowledge_bases.publisher")


class KnowledgeBasePublisher:
    """知识库发布、复制和导入编排。"""

    def __init__(
        self,
        database_connect: Callable[[], sqlite3.Connection],
        now_provider: Callable[[], int],
        store,
        searcher,
        database_path: Path,
    ) -> None:
        self._connect = database_connect
        self._now = now_provider
        self._store = store
        self._searcher = searcher
        self._database_path = database_path

    # ── 复制到教学班 ──────────────────────────────────────────────

    def copy_to_class(
        self,
        knowledge_base_id: str,
        request: CopyKnowledgeBaseRequest,
        teacher: UserView,
        require_owned_kb,
        view_for_row,
        ensure_settings,
        settings_view,
    ) -> KnowledgeBaseView:
        """在单个事务内将来源知识库和文档深复制到教学班。"""
        now = self._now()
        copied_knowledge_base_id = str(uuid.uuid4())

        with self._connect() as connection:
            source = require_owned_kb(connection, knowledge_base_id, teacher)
            if source["status"] == KnowledgeBaseStatus.ARCHIVED.value:
                raise BusinessError(
                    status_code=409, code="KNOWLEDGE_BASE_ARCHIVED",
                    message="已归档知识库不能作为新的复制来源",
                )
            target_class = connection.execute(
                "SELECT id FROM teaching_classes WHERE id = ? AND owner_teacher_id = ?",
                (request.target_class_id, teacher.id),
            ).fetchone()
            if target_class is None:
                raise BusinessError(status_code=404, code="RESOURCE_NOT_FOUND", message="教学班不存在")

            existing_copy = connection.execute(
                "SELECT id FROM knowledge_bases WHERE class_id = ? AND kind = ?",
                (request.target_class_id, KnowledgeBaseKind.CLASS_COPY.value),
            ).fetchone()
            if existing_copy is not None:
                raise BusinessError(
                    status_code=409, code="KNOWLEDGE_BASE_CLASS_ALREADY_BOUND",
                    message="该教学班已经存在知识库副本",
                )

            copied_name = request.name or source["name"]
            if source["kind"] == KnowledgeBaseKind.REUSABLE.value:
                name_conflict = connection.execute(
                    "SELECT 1 FROM knowledge_bases WHERE owner_teacher_id = ? AND kind = ? AND name = ?",
                    (teacher.id, KnowledgeBaseKind.REUSABLE.value, copied_name),
                ).fetchone()
                if name_conflict is not None and request.name is not None:
                    raise BusinessError(
                        status_code=409, code="KNOWLEDGE_BASE_NAME_CONFLICT", message="知识库名称已存在",
                    )

            connection.execute(
                """INSERT INTO knowledge_bases (
                       id, owner_teacher_id, class_id, source_knowledge_base_id,
                       kind, name, description, status, source_version,
                       archived_at, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)""",
                (copied_knowledge_base_id, teacher.id, request.target_class_id, source["id"],
                 KnowledgeBaseKind.CLASS_COPY.value, copied_name, source["description"],
                 source["status"], source["source_version"], now, now),
            )
            source_settings = ensure_settings(connection, knowledge_base_id, now)
            connection.execute(
                """UPDATE knowledge_bases
                   SET segment_mode = ?, segment_max_characters = ?,
                       segment_overlap_characters = ?, segment_separators_json = ?,
                       segment_cleaning_rules_json = ?, segment_index_version = ?,
                       segment_settings_updated_at = ?
                   WHERE id = ?""",
                (source_settings["mode"], source_settings["max_characters"],
                 source_settings["overlap_characters"], source_settings["separators_json"],
                 source_settings["cleaning_rules_json"], source_settings["index_version"],
                 now, copied_knowledge_base_id),
            )

            source_documents = connection.execute(
                """SELECT d.id, d.title, d.original_filename, d.file_format, d.parse_status,
                          document_content.markdown_content, parser_name, parser_version,
                          content_hash, error_code, error_message, d.storage_key
                   FROM knowledge_base_documents d
                   LEFT JOIN knowledge_base_document_contents document_content
                     ON document_content.document_id = d.id
                   WHERE d.knowledge_base_id = ?
                   ORDER BY d.created_at, d.id""",
                (knowledge_base_id,),
            ).fetchall()
            for source_document in source_documents:
                copied_document_id = str(uuid.uuid4())
                connection.execute(
                    """INSERT INTO knowledge_base_documents (
                           id, knowledge_base_id, source_document_id, title,
                           original_filename, file_format, parse_status,
                           parser_name, parser_version, content_hash,
                           error_code, error_message, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (copied_document_id, copied_knowledge_base_id, source_document["id"],
                     source_document["title"], source_document["original_filename"],
                     source_document["file_format"], source_document["parse_status"],
                     source_document["parser_name"], source_document["parser_version"],
                     source_document["content_hash"], source_document["error_code"],
                     source_document["error_message"], now, now),
                )
                if source_document["markdown_content"] is not None:
                    self._store.save_document_content(
                        connection, copied_document_id, source_document["markdown_content"]
                    )
                source_path = self._store.storage_path(source_document["storage_key"])
                if source_path is not None and source_path.is_file():
                    copied_storage_key = f"{copied_document_id}.md"
                    copied_storage_path = self._store.storage_path(copied_storage_key)
                    if copied_storage_path is None:
                        raise RuntimeError("复制知识库文档存储路径无法解析")
                    copied_storage_path.parent.mkdir(parents=True, exist_ok=True)
                    copied_storage_path.write_bytes(source_path.read_bytes())
                    connection.execute(
                        "UPDATE knowledge_base_documents SET storage_key = ?, storage_created_at = ? WHERE id = ?",
                        (copied_storage_key, now, copied_document_id),
                    )
                self._copy_blocks_and_chunks(connection, source_document["id"], copied_document_id, copied_knowledge_base_id)

            copied_row = require_owned_kb(connection, copied_knowledge_base_id, teacher)
            view = view_for_row(connection, copied_row)

        logger.info(
            "knowledge_base_copied source_id=%s copy_id=%s class_id=%s teacher_id=%s documents=%s",
            knowledge_base_id, copied_knowledge_base_id, request.target_class_id, teacher.id,
            len(source_documents),
        )
        return view

    @staticmethod
    def _copy_blocks_and_chunks(
        connection: sqlite3.Connection,
        source_document_id: str,
        target_document_id: str,
        target_knowledge_base_id: str,
    ) -> None:
        """复制 block、chunk、FTS 和 embedding 到目标文档。"""
        source_blocks = connection.execute(
            """SELECT ordinal, block_type, title_path_json, content,
                      page_number, source_position, line_start, line_end
               FROM knowledge_base_blocks WHERE document_id = ? ORDER BY ordinal""",
            (source_document_id,),
        ).fetchall()
        for block in source_blocks:
            connection.execute(
                """INSERT INTO knowledge_base_blocks
                   (id, document_id, ordinal, block_type, title_path_json, content,
                    page_number, source_position, line_start, line_end)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (str(uuid.uuid4()), target_document_id, block["ordinal"], block["block_type"],
                 block["title_path_json"], block["content"], block["page_number"],
                 block["source_position"], block["line_start"], block["line_end"]),
            )
        source_chunks = connection.execute(
            """SELECT id, ordinal, content, title_path_json, page_start, page_end,
                      source_position, chunk_strategy_version, index_status, document_version
               FROM knowledge_base_chunks WHERE document_id = ? ORDER BY ordinal""",
            (source_document_id,),
        ).fetchall()
        for chunk in source_chunks:
            chunk_id = str(uuid.uuid4())
            connection.execute(
                """INSERT INTO knowledge_base_chunks
                   (id, knowledge_base_id, document_id, document_version, ordinal,
                    content, title_path_json, page_start, page_end, source_position,
                    chunk_strategy_version, index_status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (chunk_id, target_knowledge_base_id, target_document_id,
                 chunk["document_version"], chunk["ordinal"], chunk["content"],
                 chunk["title_path_json"], chunk["page_start"], chunk["page_end"],
                 chunk["source_position"], chunk["chunk_strategy_version"], chunk["index_status"]),
            )
            if chunk["index_status"] == "ready":
                connection.execute(
                    """INSERT INTO knowledge_base_chunks_fts
                       (chunk_id, knowledge_base_id, content, title_path, source_position)
                       VALUES (?, ?, ?, ?, ?)""",
                    (chunk_id, target_knowledge_base_id, chunk["content"],
                     " / ".join(json.loads(chunk["title_path_json"])),
                     chunk["source_position"] or ""),
                )
            embedding = connection.execute(
                """SELECT model_name, dimensions, vector_json, status, error_code, updated_at
                   FROM knowledge_base_chunk_embeddings WHERE chunk_id = ?""",
                (chunk["id"],),
            ).fetchone()
            if embedding is not None:
                connection.execute(
                    """INSERT INTO knowledge_base_chunk_embeddings
                       (chunk_id, model_name, dimensions, vector_json, status, error_code, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (chunk_id, embedding["model_name"], embedding["dimensions"],
                     embedding["vector_json"], embedding["status"], embedding["error_code"],
                     embedding["updated_at"] or int(__import__("time").time())),
                )

    # ── 按文档导入 ────────────────────────────────────────────────

    def import_documents(
        self,
        request: ImportKnowledgeBaseDocumentsRequest,
        teacher: UserView,
        require_owned_kb,
        ensure_settings,
        view_for_row,
    ) -> KnowledgeBaseImportView:
        """只复制来源原始文件到教学班知识库，目标端随后重新解析和建索引。"""
        now = self._now()
        imported_ids: list[str] = []
        skipped_ids: list[str] = []
        source_files: list[tuple[str, str, str, str, bytes]] = []

        with self._connect() as connection:
            class_row = connection.execute(
                "SELECT id, name FROM teaching_classes WHERE id = ? AND owner_teacher_id = ?",
                (request.target_class_id, teacher.id),
            ).fetchone()
            if class_row is None:
                raise BusinessError(status_code=404, code="RESOURCE_NOT_FOUND", message="教学班不存在")

            target = connection.execute(
                "SELECT id FROM knowledge_bases WHERE class_id = ? AND owner_teacher_id = ? AND kind = 'class_copy'",
                (request.target_class_id, teacher.id),
            ).fetchone()
            target_id = target["id"] if target is not None else str(uuid.uuid4())
            if target is None:
                connection.execute(
                    """INSERT INTO knowledge_bases
                       (id, owner_teacher_id, class_id, source_knowledge_base_id,
                        kind, name, description, status, source_version,
                        archived_at, created_at, updated_at)
                       VALUES (?, ?, ?, NULL, 'class_copy', ?, ?, 'draft', 1, NULL, ?, ?)""",
                    (target_id, teacher.id, request.target_class_id,
                     f"{class_row['name']} · 教学班知识库", "由教师级知识库按文档导入的独立副本", now, now),
                )
            target_had_documents = connection.execute(
                "SELECT 1 FROM knowledge_base_documents WHERE knowledge_base_id = ? LIMIT 1",
                (target_id,),
            ).fetchone() is not None
            ensure_settings(connection, target_id, now)
            target_settings_initialized = target_had_documents

            seen_source_ids: set[str] = set()
            for item in request.items:
                source = require_owned_kb(connection, item.source_knowledge_base_id, teacher)
                if source["status"] == KnowledgeBaseStatus.ARCHIVED.value:
                    raise BusinessError(
                        status_code=409, code="KNOWLEDGE_BASE_ARCHIVED",
                        message="已归档知识库不能作为导入来源",
                    )
                for document_id in item.document_ids:
                    if document_id in seen_source_ids:
                        continue
                    seen_source_ids.add(document_id)
                    source_document = connection.execute(
                        """SELECT d.id, d.title, d.original_filename, d.file_format, d.storage_key
                           FROM knowledge_base_documents d
                           WHERE d.id = ? AND d.knowledge_base_id = ?""",
                        (document_id, item.source_knowledge_base_id),
                    ).fetchone()
                    if source_document is None:
                        raise BusinessError(status_code=404, code="RESOURCE_NOT_FOUND", message="来源文档不存在")
                    source_path = self._store.storage_path(source_document["storage_key"])
                    if source_path is None or not source_path.is_file():
                        raise BusinessError(
                            status_code=409, code="DOCUMENT_SOURCE_MISSING", message="来源文档原始文件不存在",
                        )

                    existing = connection.execute(
                        "SELECT id FROM knowledge_base_documents WHERE knowledge_base_id = ? AND source_document_id = ? ORDER BY updated_at DESC LIMIT 1",
                        (target_id, document_id),
                    ).fetchone()
                    if existing is not None and request.conflict_strategy == "skip":
                        skipped_ids.append(document_id)
                        continue
                    if existing is not None and request.conflict_strategy == "replace":
                        self._store.invalidate_document_index(connection, existing["id"])
                        connection.execute("DELETE FROM knowledge_base_documents WHERE id = ?", (existing["id"],))

                    if not target_settings_initialized:
                        source_settings = ensure_settings(connection, source["id"], now)
                        connection.execute(
                            """UPDATE knowledge_bases
                               SET segment_mode = ?, segment_max_characters = ?,
                                   segment_overlap_characters = ?, segment_separators_json = ?,
                                   segment_cleaning_rules_json = ?, segment_settings_updated_at = ?
                               WHERE id = ?""",
                            (source_settings["mode"], source_settings["max_characters"],
                             source_settings["overlap_characters"], source_settings["separators_json"],
                             source_settings["cleaning_rules_json"], now, target_id),
                        )
                        target_settings_initialized = True
                    source_files.append((
                        document_id, source_document["title"], source_document["original_filename"],
                        source_document["file_format"], source_path.read_bytes(),
                    ))

            for source_document_id, title, filename, file_format, content in source_files:
                target_document_id = str(uuid.uuid4())
                target_storage_key = f"{target_document_id}.md"
                target_path = self._store.storage_path(target_storage_key)
                if target_path is None:
                    raise RuntimeError("导入文档存储路径无法解析")
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_bytes(content)
                try:
                    connection.execute(
                        """INSERT INTO knowledge_base_documents
                           (id, knowledge_base_id, source_document_id, title,
                            original_filename, file_format, parse_status,
                            parser_name, parser_version, content_hash,
                            error_code, error_message, created_at, updated_at)
                           VALUES (?, ?, ?, ?, ?, ?, 'not_started', NULL, NULL,
                                   NULL, NULL, NULL, ?, ?)""",
                        (target_document_id, target_id, source_document_id, title,
                         filename, file_format, now, now),
                    )
                    connection.execute(
                        "UPDATE knowledge_base_documents SET storage_key = ?, storage_created_at = ? WHERE id = ?",
                        (target_storage_key, now, target_document_id),
                    )
                    imported_ids.append(target_document_id)
                except Exception:
                    target_path.unlink(missing_ok=True)
                    raise

            target_row = require_owned_kb(connection, target_id, teacher)
            target_view = view_for_row(connection, target_row)

        documents = self._store.list_documents(target_id).items
        imported_documents = [d for d in documents if d.id in imported_ids]
        logger.info(
            "knowledge_base_documents_imported target_knowledge_base_id=%s class_id=%s imported_count=%s",
            target_id, request.target_class_id, len(imported_documents),
        )
        return KnowledgeBaseImportView(
            target_knowledge_base=target_view,
            imported_documents=imported_documents,
            skipped_document_ids=skipped_ids,
        )

    # ── 发布到班级 ────────────────────────────────────────────────

    def publish_to_class(
        self,
        knowledge_base_id: str,
        class_id: str,
        knowledge_base_name: str,
    ) -> KnowledgeBasePublicationView:
        """将班级副本的已解析 Markdown 复制成独立课程内容快照。"""
        now = self._now()
        with self._connect() as connection:
            documents = connection.execute(
                """SELECT d.id, d.title, document_content.markdown_content, d.parse_status
                   FROM knowledge_base_documents d
                   LEFT JOIN knowledge_base_document_contents document_content
                     ON document_content.document_id = d.id
                   WHERE d.knowledge_base_id = ?
                   ORDER BY d.created_at, d.id""",
                (knowledge_base_id,),
            ).fetchall()
            if not documents or any(
                row["parse_status"] != "completed" or not row["markdown_content"]
                for row in documents
            ):
                raise BusinessError(
                    status_code=409, code="KNOWLEDGE_BASE_NOT_READY",
                    message="知识库仍有未完成解析的文档",
                )
            previous = connection.execute(
                "SELECT COALESCE(MAX(version), 0) FROM course_publications WHERE knowledge_base_id = ?",
                (knowledge_base_id,),
            ).fetchone()[0]
            version = int(previous) + 1
            content_ids: list[str] = []
            for document in documents:
                content_id = str(uuid.uuid4())
                content_ids.append(content_id)
                connection.execute(
                    """INSERT INTO course_contents
                       (id, class_id, content_type, publication_status, title, content,
                        due_at, description, created_at, updated_at)
                       VALUES (?, ?, 'teaching_resource', 'published', ?, ?, NULL, ?, ?, ?)""",
                    (content_id, class_id, document["title"], document["markdown_content"],
                     f"来源知识库副本：{knowledge_base_name}", now, now),
                )
            publication_id = str(uuid.uuid4())
            connection.execute(
                """INSERT INTO course_publications
                   (id, knowledge_base_id, class_id, preparation_session_id, version, created_at)
                   VALUES (?, ?, ?, NULL, ?, ?)""",
                (publication_id, knowledge_base_id, class_id, version, now),
            )
            connection.executemany(
                "INSERT INTO course_publication_contents (publication_id, content_id, ordinal) VALUES (?, ?, ?)",
                [(publication_id, content_id, ordinal) for ordinal, content_id in enumerate(content_ids)],
            )
        logger.info(
            "knowledge_base_published knowledge_base_id=%s class_id=%s version=%s",
            knowledge_base_id, class_id, version,
        )
        return KnowledgeBasePublicationView(
            publication_id=publication_id, knowledge_base_id=knowledge_base_id,
            class_id=class_id, version=version, content_ids=content_ids, created_at=now,
        )

    # ── 构建结果 ──────────────────────────────────────────────────

    def build_result(
        self,
        knowledge_base_id: str,
        processed_count: int,
        succeeded_count: int,
        failed_count: int,
        embedding_status: str,
    ) -> KnowledgeBaseBuildView:
        with self._connect() as connection:
            pending_count = connection.execute(
                "SELECT COUNT(*) FROM knowledge_base_documents WHERE knowledge_base_id = ? AND parse_status = 'not_started'",
                (knowledge_base_id,),
            ).fetchone()[0]
        return KnowledgeBaseBuildView(
            knowledge_base_id=knowledge_base_id,
            processed_count=processed_count,
            succeeded_count=succeeded_count,
            failed_count=failed_count,
            pending_count=int(pending_count),
            embedding_status=embedding_status,
        )

    # ── 教学班知识库查询 ──────────────────────────────────────────

    def get_for_class(
        self, class_id: str, teacher: UserView,
    ) -> KnowledgeBaseWorkspaceView | None:
        with self._connect() as connection:
            row = connection.execute(
                """SELECT id, owner_teacher_id, class_id, source_knowledge_base_id,
                          kind, name, description, status, source_version, created_at, updated_at
                   FROM knowledge_bases
                   WHERE class_id = ? AND owner_teacher_id = ? AND kind = 'class_copy'""",
                (class_id, teacher.id),
            ).fetchone()
            if row is None:
                return None
            documents = connection.execute(
                """SELECT id, knowledge_base_id, source_document_id, title,
                          original_filename, file_format, parse_status, error_code,
                          error_message, parser_name, parser_version, created_at, updated_at
                   FROM knowledge_base_documents
                   WHERE knowledge_base_id = ?
                   ORDER BY updated_at DESC, id DESC""",
                (row["id"],),
            ).fetchall()
        return KnowledgeBaseWorkspaceView(
            id=row["id"], owner_teacher_id=row["owner_teacher_id"],
            class_id=row["class_id"], source_knowledge_base_id=row["source_knowledge_base_id"],
            kind=row["kind"], name=row["name"], description=row["description"],
            status=row["status"], source_version=row["source_version"],
            created_at=row["created_at"], updated_at=row["updated_at"],
            documents=[KnowledgeBaseDocumentView(**dict(d)) for d in documents],
        )
