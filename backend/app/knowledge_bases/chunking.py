"""结构优先、可重复执行的 Markdown 文档切块器。"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from typing import Literal

from app.document_parsing.models import NormalizedDocument, ParsedBlock, SourceLocation


@dataclass(frozen=True)
class ChunkingConfig:
    """切块策略配置；字符数是轻量实现中的 token 近似值。"""

    max_characters: int = 2400
    overlap_characters: int = 240
    strategy_version: str = "structure-v1"
    mode: Literal["simple", "advanced"] = "simple"
    separators: tuple[str, ...] = ("#",)
    cleaning_rules: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.max_characters <= 0:
            raise ValueError("max_characters 必须大于 0")
        if self.overlap_characters < 0 or self.overlap_characters >= self.max_characters:
            raise ValueError("overlap_characters 必须小于 max_characters")


@dataclass(frozen=True)
class KnowledgeChunk:
    """可持久化的 chunk 及其来源元数据。"""

    id: str
    knowledge_base_id: str
    document_id: str
    document_version: int
    ordinal: int
    content: str
    title_path: tuple[str, ...]
    page_start: int | None
    page_end: int | None
    source_position: str | None
    chunk_strategy_version: str


def chunk_document(
    document: NormalizedDocument,
    *,
    knowledge_base_id: str,
    document_id: str,
    document_version: int,
    config: ChunkingConfig | None = None,
) -> list[KnowledgeChunk]:
    """按标题和结构块组合内容，超长块再进行确定性拆分。"""
    selected_config = config or ChunkingConfig()
    chunks: list[KnowledgeChunk] = []
    pending: list[ParsedBlock] = []
    pending_size = 0

    def flush_pending() -> None:
        nonlocal pending, pending_size
        if not pending:
            return
        chunks.append(_make_chunk(knowledge_base_id, document_id, document_version, len(chunks), pending, selected_config))
        pending = []
        pending_size = 0

    advanced_separator = _advanced_separator(selected_config)
    heading_separator_level = _heading_separator_level(advanced_separator)

    for block in document.blocks:
        if not block.content.strip():
            continue
        if (
            heading_separator_level is not None
            and block.block_type == "heading"
            and block.heading_level == heading_separator_level
        ):
            flush_pending()
        atomic = block.block_type in {"table", "code", "formula"}
        if atomic:
            pieces = [block]
        elif advanced_separator is not None and heading_separator_level is None:
            pieces = _split_by_separator(block, selected_config, advanced_separator)
        elif len(block.content) > selected_config.max_characters:
            pieces = _split_block(block, selected_config)
        else:
            pieces = [block]
        if atomic or len(pieces) > 1:
            flush_pending()
            for piece in pieces:
                chunks.append(_make_chunk(knowledge_base_id, document_id, document_version, len(chunks), [piece], selected_config))
            continue

        additional = len(block.content) + (2 if pending else 0)
        if pending and pending_size + additional > selected_config.max_characters:
            flush_pending()
        pending.append(block)
        pending_size += additional
    flush_pending()

    if not chunks and document.markdown.strip():
        fallback = ParsedBlock(
            block_id="block-0000",
            order=0,
            block_type="paragraph",
            content=document.markdown.strip(),
        )
        chunks.append(_make_chunk(knowledge_base_id, document_id, document_version, 0, [fallback], selected_config))
    return chunks


def _advanced_separator(config: ChunkingConfig) -> str | None:
    """高级分段只取一个当前分隔符，避免算法和教师选择出现分歧。"""
    if config.mode != "advanced" or not config.separators:
        return None
    return config.separators[0]


def _heading_separator_level(separator: str | None) -> int | None:
    """把 Markdown 标题分隔符映射为精确标题层级。"""
    if separator and 1 <= len(separator) <= 6 and set(separator) == {"#"}:
        return len(separator)
    return None


def _split_by_separator(
    block: ParsedBlock, config: ChunkingConfig, separator: str
) -> list[ParsedBlock]:
    """按当前唯一标识切分，并在单个结果仍过长时回退到长度保护。"""
    if not separator or separator not in block.content:
        return _split_block(block, config) if len(block.content) > config.max_characters else [block]

    pieces: list[ParsedBlock] = []
    start = 0
    while start < len(block.content):
        separator_index = block.content.find(separator, start)
        end = len(block.content) if separator_index < 0 else separator_index + len(separator)
        content = block.content[start:end].strip()
        if content:
            piece = ParsedBlock(
                block_id=f"{block.block_id}-{len(pieces):04d}",
                order=block.order,
                block_type=block.block_type,
                content=content,
                title_path=block.title_path,
                source=block.source,
                heading_level=block.heading_level,
            )
            if len(content) > config.max_characters:
                pieces.extend(_split_block(piece, config))
            else:
                pieces.append(piece)
        if end >= len(block.content):
            break
        start = end
    return pieces


def _split_block(block: ParsedBlock, config: ChunkingConfig) -> list[ParsedBlock]:
    content = block.content
    pieces: list[ParsedBlock] = []
    start = 0
    while start < len(content):
        end = min(start + config.max_characters, len(content))
        if end < len(content):
            boundary_candidates = [
                content.rfind(separator, start, end)
                for separator in (config.separators if config.mode == "advanced" else ("\n", "。", " "))
            ]
            boundary = max(boundary_candidates + [content.rfind(" ", start, end)])
            if boundary > start + config.max_characters // 2:
                end = boundary + 1
        piece = content[start:end].strip()
        if piece:
            source = block.source
            pieces.append(
                ParsedBlock(
                    block_id=f"{block.block_id}-{len(pieces):04d}",
                    order=block.order,
                    block_type=block.block_type,
                    content=piece,
                    title_path=block.title_path,
                    source=source,
                    heading_level=block.heading_level,
                )
            )
        if end >= len(content):
            break
        next_start = max(end - config.overlap_characters, start + 1)
        start = next_start
    return pieces


def _make_chunk(
    knowledge_base_id: str,
    document_id: str,
    document_version: int,
    ordinal: int,
    blocks: list[ParsedBlock],
    config: ChunkingConfig,
) -> KnowledgeChunk:
    text = "\n\n".join(block.content for block in blocks).strip()
    title_path = blocks[-1].title_path or blocks[0].title_path
    sources = [block.source for block in blocks if block.source is not None]
    pages = [source.page_number for source in sources if source.page_number is not None]
    lines = [source for source in sources if source.line_start is not None or source.line_end is not None]
    source_position = _source_position(lines)
    stable_key = f"{document_id}:{ordinal}:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"
    chunk_id = str(uuid.uuid5(uuid.NAMESPACE_URL, stable_key))
    return KnowledgeChunk(
        id=chunk_id,
        knowledge_base_id=knowledge_base_id,
        document_id=document_id,
        document_version=document_version,
        ordinal=ordinal,
        content=text,
        title_path=title_path,
        page_start=min(pages) if pages else None,
        page_end=max(pages) if pages else None,
        source_position=source_position,
        chunk_strategy_version=config.strategy_version,
    )


def _source_position(sources: list[SourceLocation]) -> str | None:
    labels = [source.label for source in sources if source.label]
    if labels:
        return "; ".join(dict.fromkeys(labels))
    starts = [source.line_start for source in sources if source.line_start is not None]
    ends = [source.line_end for source in sources if source.line_end is not None]
    if starts or ends:
        return f"lines {min(starts) if starts else min(ends)}-{max(ends) if ends else max(starts)}"
    return None
