"""备课高亮管理模块：教学重点的 CRUD 和段落查询。

从 PreparationSessionModule 提取，聚合教学重点相关的业务逻辑。
"""
from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from collections.abc import Callable

from app.common.errors import BusinessError
from app.teaching_classes.models import (
    AddHighlightRequest,
    HighlightView,
    ParseStatus,
    PreparationSessionParagraphWithHighlightsView,
    PreparationSessionParsingResultWithHighlightsView,
)
from app.teaching_classes.preparation_state import PreparationSessionStateStore


logger = logging.getLogger("course_agent.teaching_classes.preparation_highlights")


class HighlightManager:
    """教学重点管理：高亮 CRUD、段落查询。"""

    def __init__(
        self,
        now_provider: Callable[[], int],
    ) -> None:
        self._now = now_provider
        self._state = PreparationSessionStateStore()

    def _require_parsed(self, session: sqlite3.Row) -> None:
        """验证备课会话已完成解析。"""
        if session["parse_status"] != ParseStatus.COMPLETED.value:
            raise BusinessError(
                status_code=400,
                code="PREPARATION_SESSION_NOT_PARSED",
                message="备课会话未完成解析，无法进行此操作",
            )

    @staticmethod
    def _load_paragraph_rows(
        connection: sqlite3.Connection, session_id: str
    ) -> list[dict[str, object]]:
        """读取段落及文档归属。"""
        return [
            dict(row)
            for row in connection.execute(
                """SELECT p.ordinal, p.document_id, d.original_filename AS document_filename,
                          p.block_type, p.content
                   FROM preparation_session_segments p
                   LEFT JOIN knowledge_base_documents d ON d.id = p.document_id
                   WHERE p.session_id = ?
                   ORDER BY p.ordinal""",
                (session_id,),
            ).fetchall()
        ]

    @staticmethod
    def _to_view(paragraph_rows, highlight_rows, highlights_by_paragraph):
        """构建带教学重点的段落视图（不含 session，由调用方填充）。"""
        paragraphs_with_highlights = []
        for row in paragraph_rows:
            po = row["ordinal"]
            highlights = highlights_by_paragraph.get(po, [])
            paragraphs_with_highlights.append(
                PreparationSessionParagraphWithHighlightsView(
                    ordinal=po,
                    document_id=row["document_id"],
                    document_filename=row["document_filename"],
                    block_type=row["block_type"],
                    content=row["content"],
                    highlights=highlights,
                    has_highlights=len(highlights) > 0,
                )
            )
        return paragraphs_with_highlights, len(highlight_rows)

    def get_paragraphs_with_highlights(
        self,
        connection: sqlite3.Connection,
        session: sqlite3.Row,
        session_view: PreparationSessionParsingResultWithHighlightsView | None = None,
    ) -> tuple[list, int]:
        """读取已完成会话的有序段落和教学重点，返回 (paragraphs, total_highlights)。"""
        if session["parse_status"] != ParseStatus.COMPLETED.value:
            return [], 0

        paragraph_rows = self._load_paragraph_rows(connection, session["id"])
        highlight_rows = sorted(
            self._state.load_highlights(connection, session["id"]),
            key=lambda item: (item["paragraphOrdinal"], item["startOffset"], item["endOffset"]),
        )

        highlights_by_paragraph: dict[int, list[HighlightView]] = {}
        for row in highlight_rows:
            po = row["paragraphOrdinal"]
            if po not in highlights_by_paragraph:
                highlights_by_paragraph[po] = []
            highlights_by_paragraph[po].append(
                HighlightView(
                    id=row["id"],
                    paragraph_ordinal=po,
                    start_offset=row["startOffset"],
                    end_offset=row["endOffset"],
                    created_at=row["createdAt"],
                )
            )

        paragraphs_with_highlights, total = self._to_view(paragraph_rows, highlight_rows, highlights_by_paragraph)
        return paragraphs_with_highlights, total

    def add_highlight(
        self,
        connection: sqlite3.Connection,
        session: sqlite3.Row,
        request: AddHighlightRequest,
    ) -> HighlightView:
        """新增教学重点。"""
        now = self._now()
        self._require_parsed(session)

        paragraph = connection.execute(
            "SELECT content FROM preparation_session_segments WHERE session_id=? AND ordinal=?",
            (session["id"], request.paragraph_ordinal),
        ).fetchone()
        if paragraph is None:
            raise BusinessError(status_code=404, code="PARAGRAPH_NOT_FOUND", message="段落不存在")

        content_length = len(paragraph["content"])
        if request.start_offset >= content_length:
            raise BusinessError(status_code=400, code="INVALID_OFFSET_RANGE", message="开始偏移超出段落长度")
        if request.end_offset > content_length:
            raise BusinessError(status_code=400, code="INVALID_OFFSET_RANGE", message="结束偏移超出段落长度")
        if request.start_offset == request.end_offset:
            raise BusinessError(status_code=400, code="EMPTY_HIGHLIGHT_RANGE", message="教学重点区间不能为空")

        highlights = self._state.load_highlights(connection, session["id"])
        overlapping = [
            h for h in highlights
            if h["paragraphOrdinal"] == request.paragraph_ordinal
            and h["startOffset"] < request.end_offset
            and h["endOffset"] > request.start_offset
            and (h["startOffset"] != request.start_offset or h["endOffset"] != request.end_offset)
        ]
        if overlapping:
            raise BusinessError(status_code=409, code="HIGHLIGHT_OVERLAP", message="教学重点与现有重点重叠")

        existing = next(
            (h for h in highlights if h["paragraphOrdinal"] == request.paragraph_ordinal
             and h["startOffset"] == request.start_offset and h["endOffset"] == request.end_offset),
            None,
        )
        if existing:
            raise BusinessError(status_code=409, code="HIGHLIGHT_DUPLICATE", message="教学重点已存在")

        highlight_id = str(uuid.uuid4())
        highlights.append({
            "id": highlight_id,
            "paragraphOrdinal": request.paragraph_ordinal,
            "startOffset": request.start_offset,
            "endOffset": request.end_offset,
            "createdAt": now,
        })
        self._state.save_highlights(connection, session, highlights, now)

        logger.info(
            "highlight_added highlight_id=%s session_id=%s paragraph_ordinal=%s start=%s end=%s",
            highlight_id, session["id"], request.paragraph_ordinal,
            request.start_offset, request.end_offset,
        )

        return HighlightView(
            id=highlight_id,
            paragraph_ordinal=request.paragraph_ordinal,
            start_offset=request.start_offset,
            end_offset=request.end_offset,
            created_at=now,
        )

    def remove_highlight(
        self,
        connection: sqlite3.Connection,
        session: sqlite3.Row,
        highlight_id: str,
    ) -> None:
        """取消教学重点。"""
        self._require_parsed(session)
        highlights = self._state.load_highlights(connection, session["id"])
        highlight = next((h for h in highlights if h["id"] == highlight_id), None)
        if highlight is None:
            raise BusinessError(status_code=404, code="HIGHLIGHT_NOT_FOUND", message="教学重点不存在")

        highlights.remove(highlight)
        self._state.save_highlights(connection, session, highlights, self._now())

        logger.info(
            "highlight_removed highlight_id=%s session_id=%s",
            highlight_id, session["id"],
        )
