"""知识库文档存储管理模块。

从 KnowledgeBaseService 提取的独立文档管理模块，负责文档 CRUD、
上传/替换/删除、解析状态管理、文件存储路径管理。
"""
from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import uuid
from collections.abc import Callable
from pathlib import Path

from app.auth.models import UserView
from app.common.errors import BusinessError
from app.document_parsing.models import NormalizedDocument, ParsedBlock, SourceLocation
from app.knowledge_bases.models import (
    KnowledgeBaseDocumentView,
    KnowledgeBaseDocumentListView,
    KnowledgeBaseDocument,
    DocumentStatus,
    UpdateKnowledgeBaseDocumentRequest,
)
from app.knowledge_bases.chunking import ChunkingConfig, chunk_document


logger = logging.getLogger("course_agent.knowledge_bases.document_store")


class KnowledgeBaseDocumentStore:
    """知识库文档存储：文档 CRUD、文件存储、解析状态管理。"""

    def __init__(
        self,
        database_connect: Callable[[], sqlite3.Connection],
        now_provider: Callable[[], int],
        database_path: Path,
    ) -> None:
        self._connect = database_connect
        self._now = now_provider
        self._database_path = database_path

    # ── 文档视图映射 ──────────────────────────────────────────────

    @staticmethod
    def resource_not_found(message: str = "知识库不存在") -> BusinessError:
        return BusinessError(status_code=404, code="RESOURCE_NOT_FOUND", message=message)

    @staticmethod
    def document_view(row: sqlite3.Row) -> KnowledgeBaseDocumentView:
        """统一把文档行映射为完整 DTO，避免列表、详情和上传返回漂移。"""
        values = dict(row)
        values.setdefault("title", values.get("original_filename", "未命名文档"))
        values.setdefault("version", 1)
        values.setdefault("content_hash", None)
        values.setdefault("markdown_content", None)
        return KnowledgeBaseDocumentView(**values)

    # ── 存储路径 ──────────────────────────────────────────────────

    def storage_path(self, storage_key: str | None) -> Path | None:
        """把数据库中的相对存储键解析到应用私有目录。"""
        if not storage_key:
            return None
        return self._database_path.parent / "knowledge-base-uploads" / Path(storage_key).name

    # ── 文档内容操作 ──────────────────────────────────────────────

    @staticmethod
    def save_document_content(connection: sqlite3.Connection, document_id: str, markdown_content: str) -> None:
        connection.execute(
            """INSERT INTO knowledge_base_document_contents(document_id, markdown_content)
               VALUES (?, ?)
               ON CONFLICT(document_id) DO UPDATE SET markdown_content = excluded.markdown_content""",
            (document_id, markdown_content),
        )

    @staticmethod
    def clear_document_content(connection: sqlite3.Connection, document_id: str) -> None:
        connection.execute(
            "DELETE FROM knowledge_base_document_contents WHERE document_id = ?",
            (document_id,),
        )

    # ── 索引失效 ──────────────────────────────────────────────────

    @staticmethod
    def invalidate_document_index(connection: sqlite3.Connection, document_id: str) -> None:
        """在文档内容失效时清理 block、chunk 和 FTS 派生结构。"""
        KnowledgeBaseDocumentStore.invalidate_document_chunks(connection, document_id)
        connection.execute(
            "DELETE FROM knowledge_base_blocks WHERE document_id = ?", (document_id,)
        )

    @staticmethod
    def invalidate_document_chunks(connection: sqlite3.Connection, document_id: str) -> None:
        """只清理可重建的 chunk/FTS 索引，保留结构化 block。"""
        connection.execute(
            "DELETE FROM knowledge_base_chunks_fts WHERE chunk_id IN (SELECT id FROM knowledge_base_chunks WHERE document_id = ?)",
            (document_id,),
        )
        connection.execute(
            "DELETE FROM knowledge_base_chunks WHERE document_id = ?", (document_id,)
        )

    # ── 文档 CRUD ─────────────────────────────────────────────────

    def list_documents(
        self, knowledge_base_id: str
    ) -> KnowledgeBaseDocumentListView:
        """按知识库边界返回文档。"""
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT id, knowledge_base_id, source_document_id, title,
                          original_filename, file_format, parse_status, error_code,
                          error_message, parser_name, parser_version, updated_at,
                          created_at, version, content_hash, document_content.markdown_content
                   FROM knowledge_base_documents
                   LEFT JOIN knowledge_base_document_contents document_content
                     ON document_content.document_id = knowledge_base_documents.id
                   WHERE knowledge_base_id = ?
                   ORDER BY updated_at DESC, id DESC""",
                (knowledge_base_id,),
            ).fetchall()
        return KnowledgeBaseDocumentListView(
            items=[self.document_view(row) for row in rows]
        )

    def get_document(
        self, document_id: str, knowledge_base_id: str
    ) -> KnowledgeBaseDocumentView:
        """读取指定文档。"""
        with self._connect() as connection:
            row = connection.execute(
                """SELECT id, knowledge_base_id, source_document_id, title,
                          original_filename, file_format, parse_status, error_code,
                          error_message, parser_name, parser_version, updated_at,
                          created_at, version, content_hash, document_content.markdown_content
                   FROM knowledge_base_documents
                   LEFT JOIN knowledge_base_document_contents document_content
                     ON document_content.document_id = knowledge_base_documents.id
                   WHERE id = ? AND knowledge_base_id = ?""",
                (document_id, knowledge_base_id),
            ).fetchone()
        if row is None:
            raise self.resource_not_found("文档不存在")
        return self.document_view(row)

    def get_document_source_path(
        self, document_id: str, knowledge_base_id: str
    ) -> Path:
        """读取文档受控原文件路径。"""
        with self._connect() as connection:
            row = connection.execute(
                """SELECT d.storage_key
                   FROM knowledge_base_documents d
                   WHERE d.id = ? AND d.knowledge_base_id = ?""",
                (document_id, knowledge_base_id),
            ).fetchone()
        if row is None:
            raise self.resource_not_found("文档原始文件不存在")
        storage_path = self.storage_path(row["storage_key"])
        if storage_path is None:
            raise self.resource_not_found("文档原始文件不存在")
        return storage_path

    def save_uploaded_document(
        self,
        knowledge_base_id: str,
        filename: str,
        content: bytes,
    ) -> KnowledgeBaseDocumentView:
        """只保存原始 Markdown 并创建待解析记录。"""
        now = self._now()
        document_id = str(uuid.uuid4())
        upload_dir = self._database_path.parent / "knowledge-base-uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        storage_key = f"{document_id}.md"
        storage_path = upload_dir / storage_key
        try:
            storage_path.write_bytes(content)
            with self._connect() as connection:
                connection.execute(
                    """INSERT INTO knowledge_base_documents
                       (id, knowledge_base_id, source_document_id, title, original_filename,
                        file_format, parse_status, parser_name,
                        parser_version, content_hash, error_code, error_message, created_at, updated_at)
                       VALUES (?, ?, NULL, ?, ?, 'markdown', 'not_started', NULL, NULL, NULL, NULL, NULL, ?, ?)""",
                    (document_id, knowledge_base_id, Path(filename).stem[:200] or filename,
                     filename, now, now),
                )
                connection.execute(
                    "UPDATE knowledge_base_documents SET storage_key = ?, storage_created_at = ? WHERE id = ?",
                    (storage_key, now, document_id),
                )
                row = connection.execute(
                    """SELECT id, knowledge_base_id, source_document_id, title,
                              original_filename, file_format, parse_status, error_code,
                              error_message, parser_name, parser_version, updated_at,
                              created_at, version, content_hash
                       FROM knowledge_base_documents WHERE id = ?""",
                    (document_id,),
                ).fetchone()
        except Exception:
            storage_path.unlink(missing_ok=True)
            raise
        logger.info(
            "knowledge_base_document_uploaded document_id=%s knowledge_base_id=%s",
            document_id, knowledge_base_id,
        )
        return self.document_view(row)

    def update_document(
        self,
        knowledge_base_id: str,
        document_id: str,
        request: UpdateKnowledgeBaseDocumentRequest,
    ) -> KnowledgeBaseDocumentView:
        """编辑标题或 Markdown；内容变化递增版本并清除旧索引。"""
        if request.title is None and request.markdown_content is None:
            raise BusinessError(
                status_code=400, code="DOCUMENT_UPDATE_EMPTY",
                message="至少提供标题或 Markdown 内容",
            )
        now = self._now()
        with self._connect() as connection:
            row = connection.execute(
                """SELECT d.id, d.title, d.version, d.storage_key
                   FROM knowledge_base_documents d
                   WHERE d.id = ? AND d.knowledge_base_id = ?""",
                (document_id, knowledge_base_id),
            ).fetchone()
            if row is None:
                raise self.resource_not_found("文档不存在")

            next_title = request.title or row["title"]
            content_hash: str | None = None
            if request.markdown_content is not None:
                content = request.markdown_content.encode("utf-8")
                if not content.strip():
                    raise BusinessError(
                        status_code=400, code="FILE_EMPTY", message="Markdown 内容不能为空",
                    )
                storage_path = self.storage_path(row["storage_key"])
                if storage_path is None:
                    raise BusinessError(
                        status_code=409, code="DOCUMENT_SOURCE_MISSING", message="文档原始文件不存在",
                    )
                original_content = storage_path.read_bytes()
                try:
                    storage_path.write_bytes(content)
                    content_hash = hashlib.sha256(content).hexdigest()
                    self.invalidate_document_index(connection, document_id)
                    connection.execute(
                        """UPDATE knowledge_base_documents
                           SET title = ?, version = version + 1, parse_status = 'not_started',
                               parser_name = NULL, parser_version = NULL,
                               content_hash = ?, error_code = NULL, error_message = NULL, updated_at = ?
                           WHERE id = ? AND knowledge_base_id = ?""",
                        (next_title, content_hash, now, document_id, knowledge_base_id),
                    )
                    self.clear_document_content(connection, document_id)
                    connection.commit()
                except Exception:
                    storage_path.write_bytes(original_content)
                    raise
            else:
                connection.execute(
                    """UPDATE knowledge_base_documents
                       SET title = ?, updated_at = ?
                       WHERE id = ? AND knowledge_base_id = ?""",
                    (next_title, now, document_id, knowledge_base_id),
                )
        logger.info(
            "knowledge_base_document_updated knowledge_base_id=%s document_id=%s content_changed=%s",
            knowledge_base_id, document_id, request.markdown_content is not None,
        )
        return self.get_document(document_id, knowledge_base_id)

    def replace_document_source(
        self,
        knowledge_base_id: str,
        document_id: str,
        filename: str,
        content: bytes,
    ) -> KnowledgeBaseDocumentView:
        """替换受控原始 Markdown 文件，并建立新的文档版本边界。"""
        if not content:
            raise BusinessError(status_code=400, code="FILE_EMPTY", message="上传文件不能为空")
        now = self._now()
        with self._connect() as connection:
            row = connection.execute(
                """SELECT d.id, d.storage_key
                   FROM knowledge_base_documents d
                   WHERE d.id = ? AND d.knowledge_base_id = ?""",
                (document_id, knowledge_base_id),
            ).fetchone()
            if row is None:
                raise self.resource_not_found("文档不存在")
            storage_path = self.storage_path(row["storage_key"])
            if storage_path is None:
                raise BusinessError(
                    status_code=409, code="DOCUMENT_SOURCE_MISSING", message="文档原始文件不存在",
                )
            original_content = storage_path.read_bytes()
            try:
                storage_path.write_bytes(content)
                self.invalidate_document_index(connection, document_id)
                connection.execute(
                    """UPDATE knowledge_base_documents
                       SET original_filename = ?, version = version + 1, parse_status = 'not_started',
                           parser_name = NULL, parser_version = NULL,
                           content_hash = ?, error_code = NULL, error_message = NULL, updated_at = ?
                       WHERE id = ? AND knowledge_base_id = ?""",
                    (filename, hashlib.sha256(content).hexdigest(), now, document_id, knowledge_base_id),
                )
                self.clear_document_content(connection, document_id)
                connection.commit()
            except Exception:
                storage_path.write_bytes(original_content)
                raise
        return self.get_document(document_id, knowledge_base_id)

    def delete_document(self, knowledge_base_id: str, document_id: str) -> None:
        """删除文档及其分段、FTS 记录和受控原始文件。"""
        with self._connect() as connection:
            row = connection.execute(
                """SELECT d.id, d.storage_key
                   FROM knowledge_base_documents d
                   WHERE d.id = ? AND d.knowledge_base_id = ?""",
                (document_id, knowledge_base_id),
            ).fetchone()
            if row is None:
                raise self.resource_not_found("文档不存在")
            self.invalidate_document_index(connection, document_id)
            # 班级文档是独立副本；删除来源文档时只解除来源追踪
            connection.execute(
                "UPDATE knowledge_base_documents SET source_document_id = NULL WHERE source_document_id = ?",
                (document_id,),
            )
            connection.execute(
                "DELETE FROM knowledge_base_documents WHERE id = ? AND knowledge_base_id = ?",
                (document_id, knowledge_base_id),
            )
            storage_path = self.storage_path(row["storage_key"])
        if storage_path is not None:
            storage_path.unlink(missing_ok=True)
        logger.info(
            "knowledge_base_document_deleted knowledge_base_id=%s document_id=%s",
            knowledge_base_id, document_id,
        )

    # ── 文档解析状态管理 ──────────────────────────────────────────

    def mark_document_parsing(self, document_id: str) -> int:
        now = self._now()
        with self._connect() as connection:
            row = connection.execute(
                """SELECT d.id, d.version FROM knowledge_base_documents d
                   JOIN knowledge_bases kb ON kb.id = d.knowledge_base_id
                   WHERE d.id = ?""",
                (document_id,),
            ).fetchone()
            if row is None:
                raise self.resource_not_found("文档不存在")
            cursor = connection.execute(
                """UPDATE knowledge_base_documents
                   SET parse_status = 'parsing', error_code = NULL, error_message = NULL, updated_at = ?
                   WHERE id = ? AND parse_status IN ('not_started', 'failed')""",
                (now, document_id),
            )
            if cursor.rowcount != 1:
                raise BusinessError(
                    status_code=409, code="DOCUMENT_PARSING", message="文档正在解析，请稍后重试",
                )
            return int(row["version"])

    def complete_uploaded_document(
        self,
        document_id: str,
        normalized_document: NormalizedDocument,
        *,
        expected_version: int,
        build_index: bool = True,
        chunking_config: ChunkingConfig | None = None,
    ) -> KnowledgeBaseDocumentView:
        """保存解析结果；按需预览时可暂不建立最终索引。"""
        now = self._now()
        with self._connect() as connection:
            row = connection.execute(
                """SELECT d.knowledge_base_id, d.original_filename, d.version, d.parse_status
                   FROM knowledge_base_documents d
                   WHERE d.id = ?""",
                (document_id,),
            ).fetchone()
            if row is None:
                raise self.resource_not_found("文档不存在")
            if row["version"] != expected_version or row["parse_status"] != "parsing":
                raise BusinessError(
                    status_code=409, code="DOCUMENT_VERSION_CONFLICT",
                    message="文档版本已变化，请重新解析",
                )
            knowledge_base_id = row["knowledge_base_id"]
            # 清除旧派生数据
            connection.execute(
                "DELETE FROM knowledge_base_chunks_fts WHERE chunk_id IN (SELECT id FROM knowledge_base_chunks WHERE document_id = ?)",
                (document_id,),
            )
            connection.execute("DELETE FROM knowledge_base_chunks WHERE document_id = ?", (document_id,))
            connection.execute("DELETE FROM knowledge_base_blocks WHERE document_id = ?", (document_id,))
            connection.execute(
                """UPDATE knowledge_base_documents
                   SET parse_status = 'completed', parser_name = ?,
                       parser_version = ?, content_hash = ?, error_code = NULL,
                       error_message = NULL, updated_at = ?
                   WHERE id = ?""",
                (normalized_document.parser_name, normalized_document.parser_version,
                 normalized_document.content_sha256, now, document_id),
            )
            self.save_document_content(connection, document_id, normalized_document.markdown)
            for block in normalized_document.blocks:
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
            if build_index:
                config = chunking_config or ChunkingConfig()
                chunks = chunk_document(
                    normalized_document,
                    knowledge_base_id=knowledge_base_id,
                    document_id=document_id,
                    document_version=row["version"],
                    config=config,
                )
                for chunk in chunks:
                    connection.execute(
                        """INSERT INTO knowledge_base_chunks
                           (id, knowledge_base_id, document_id, document_version, ordinal,
                            content, title_path_json, page_start, page_end, source_position,
                            chunk_strategy_version, index_status)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ready')""",
                        (chunk.id, knowledge_base_id, document_id, row["version"],
                         chunk.ordinal, chunk.content, json.dumps(list(chunk.title_path), ensure_ascii=False),
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
            result = connection.execute(
                """SELECT id, knowledge_base_id, source_document_id, title,
                          original_filename, file_format, parse_status, error_code,
                          error_message, parser_name, parser_version, created_at, updated_at
                   FROM knowledge_base_documents WHERE id = ?""",
                (document_id,),
            ).fetchone()
        return KnowledgeBaseDocumentView(**dict(result))

    def mark_document_failed(
        self, document_id: str, error_code: str, error_message: str,
        *, expected_version: int | None = None,
    ) -> KnowledgeBaseDocumentView:
        now = self._now()
        with self._connect() as connection:
            row = connection.execute(
                """SELECT d.id FROM knowledge_base_documents d
                   WHERE d.id = ?""",
                (document_id,),
            ).fetchone()
            if row is None:
                raise self.resource_not_found("文档不存在")
            cursor = connection.execute(
                """UPDATE knowledge_base_documents
                   SET parse_status = 'failed', error_code = ?, error_message = ?, updated_at = ?
                   WHERE id = ? AND (? IS NULL OR (version = ? AND parse_status = 'parsing'))""",
                (error_code, error_message, now, document_id, expected_version, expected_version),
            )
            if cursor.rowcount != 1:
                raise BusinessError(
                    status_code=409, code="DOCUMENT_VERSION_CONFLICT", message="文档版本已变化，请重新解析",
                )
            result = connection.execute(
                """SELECT id, knowledge_base_id, source_document_id, title,
                          original_filename, file_format, parse_status, error_code,
                          error_message, parser_name, parser_version, created_at, updated_at
                   FROM knowledge_base_documents WHERE id = ?""",
                (document_id,),
            ).fetchone()
        return KnowledgeBaseDocumentView(**dict(result))

    def save_failed_document(
        self,
        knowledge_base_id: str,
        filename: str,
        file_format: str,
        content: bytes,
        error_code: str,
    ) -> KnowledgeBaseDocumentView:
        """保留失败任务和受控输入文件。"""
        now = self._now()
        document_id = str(uuid.uuid4())
        upload_dir = self._database_path.parent / "knowledge-base-uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        storage_key = f"{document_id}{Path(filename).suffix.lower()}"
        storage_path = upload_dir / storage_key
        storage_path.write_bytes(content)
        try:
            with self._connect() as connection:
                connection.execute(
                    """INSERT INTO knowledge_base_documents
                       (id, knowledge_base_id, source_document_id, title, original_filename,
                        file_format, parse_status, parser_name,
                        parser_version, content_hash, error_code, created_at, updated_at)
                       VALUES (?, ?, NULL, ?, ?, ?, 'failed', NULL, NULL, NULL, ?, ?, ?)""",
                    (document_id, knowledge_base_id, Path(filename).stem[:200] or filename,
                     filename, file_format, error_code, now, now),
                )
                connection.execute(
                    "UPDATE knowledge_base_documents SET storage_key = ?, storage_created_at = ? WHERE id = ?",
                    (storage_key, now, document_id),
                )
                row = connection.execute(
                    """SELECT id, knowledge_base_id, source_document_id, title,
                              original_filename, file_format, parse_status, error_code,
                              error_message, parser_name, parser_version, created_at, updated_at
                       FROM knowledge_base_documents WHERE id = ?""",
                    (document_id,),
                ).fetchone()
        except Exception:
            storage_path.unlink(missing_ok=True)
            raise
        return KnowledgeBaseDocumentView(**dict(row))

    def get_failed_document_source(
        self, document_id: str
    ) -> tuple[str, str, str, Path]:
        with self._connect() as connection:
            row = connection.execute(
                """SELECT d.knowledge_base_id, d.original_filename, d.file_format, d.storage_key
                   FROM knowledge_base_documents d
                   WHERE d.id = ? AND d.parse_status = 'failed'""",
                (document_id,),
            ).fetchone()
        if row is None:
            raise self.resource_not_found("失败文档不存在")
        storage_path = self.storage_path(row["storage_key"])
        if storage_path is None:
            raise self.resource_not_found("失败文档原始文件不存在")
        return row["knowledge_base_id"], row["original_filename"], row["file_format"], storage_path

    def list_build_documents(
        self, knowledge_base_id: str
    ) -> list[tuple[str, Path]]:
        """读取导入流程待解析文档的受控原始文件路径。"""
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT d.id, d.storage_key
                   FROM knowledge_base_documents d
                   WHERE d.knowledge_base_id = ? AND d.parse_status = 'not_started'
                   ORDER BY d.created_at, d.id""",
                (knowledge_base_id,),
            ).fetchall()
        documents: list[tuple[str, Path]] = []
        for row in rows:
            storage_path = self.storage_path(row["storage_key"])
            if storage_path is not None:
                documents.append((row["id"], storage_path))
        return documents

    # ── NormalizedDocument 重建 ───────────────────────────────────

    @staticmethod
    def normalized_from_rows(
        markdown: str, rows: list[sqlite3.Row], content_hash: str | None
    ) -> NormalizedDocument:
        lines = markdown.replace("\r\n", "\n").replace("\r", "\n").split("\n")

        def heading_level(line_start: int | None) -> int | None:
            if line_start is None or line_start < 1 or line_start > len(lines):
                return None
            import re as _re
            match = _re.match(r"^\s*(#{1,6})(?:\s+|$)", lines[line_start - 1])
            return len(match.group(1)) if match else None

        blocks = tuple(
            ParsedBlock(
                block_id=f"block-{row['ordinal']:04d}",
                order=row["ordinal"],
                block_type=row["block_type"],
                content=row["content"],
                title_path=tuple(json.loads(row["title_path_json"])),
                source=SourceLocation(
                    page_number=row["page_number"],
                    line_start=row["line_start"],
                    line_end=row["line_end"],
                    label=row["source_position"],
                ),
                heading_level=heading_level(row["line_start"])
                if row["block_type"] == "heading"
                else None,
            )
            for row in rows
        )
        return NormalizedDocument(
            markdown=markdown,
            blocks=blocks,
            parser_name="markdown",
            parser_version="stored-v1",
            content_sha256=content_hash
            or hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
        )

    # ── 文档内容加载 ──────────────────────────────────────────────

    def load_segment_source(
        self, connection: sqlite3.Connection, knowledge_base_id: str, document_id: str
    ) -> tuple[sqlite3.Row, NormalizedDocument]:
        document = connection.execute(
            """SELECT d.id, d.original_filename, d.version, d.parse_status,
                      document_content.markdown_content, d.content_hash
               FROM knowledge_base_documents d
               LEFT JOIN knowledge_base_document_contents document_content
                 ON document_content.document_id = d.id
               WHERE id = ? AND knowledge_base_id = ?""",
            (document_id, knowledge_base_id),
        ).fetchone()
        if document is None:
            raise self.resource_not_found("文档不存在")
        if document["parse_status"] != "completed" or not document["markdown_content"]:
            raise BusinessError(
                status_code=409, code="DOCUMENT_NOT_READY",
                message="文档尚未完成解析，暂时不能预览或重建分段",
            )
        blocks = connection.execute(
            """SELECT ordinal, block_type, title_path_json, content, page_number,
                      source_position, line_start, line_end
               FROM knowledge_base_blocks
               WHERE document_id = ?
               ORDER BY ordinal""",
            (document_id,),
        ).fetchall()
        return document, self.normalized_from_rows(
            document["markdown_content"], blocks, document["content_hash"]
        )
