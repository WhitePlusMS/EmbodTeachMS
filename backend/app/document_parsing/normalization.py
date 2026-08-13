"""把本地 Markdown 和外部解析服务结果归一化为内部文档模型。"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping, Sequence

from .models import NormalizedDocument, ParsedBlock, SourceLocation


def normalize_markdown_document(
    markdown: str,
    *,
    parser_name: str,
    parser_version: str,
) -> NormalizedDocument:
    """规范化 Markdown 文本并生成稳定的块标识。"""
    normalized_markdown = _normalize_markdown(markdown)
    digest = hashlib.sha256(normalized_markdown.encode("utf-8")).hexdigest()
    return NormalizedDocument(
        markdown=normalized_markdown,
        blocks=(),
        parser_name=parser_name,
        parser_version=parser_version,
        content_sha256=digest,
    )


def normalize_external_document(
    payload: Mapping[str, object],
    *,
    parser_name: str,
    default_parser_version: str,
) -> NormalizedDocument:
    """适配已验证的解析服务 DTO，不把供应商字段泄露给业务层。

    服务可以提供完整 Markdown、结构化 blocks 或两者。两者同时存在时，
    Markdown 作为主内容，blocks 只补充检索所需的结构和来源信息。
    """
    markdown_value = _first_string(payload, ("markdown", "content"))
    raw_blocks = payload.get("blocks")
    blocks = _normalize_blocks(raw_blocks)
    if not markdown_value and blocks:
        markdown_value = _blocks_to_markdown(blocks)
    if not markdown_value:
        raise ValueError("解析服务未返回有效 Markdown 内容")

    normalized_markdown = _normalize_markdown(markdown_value)
    digest = hashlib.sha256(normalized_markdown.encode("utf-8")).hexdigest()
    parser_version = _first_string(
        payload,
        ("parser_version", "version"),
    ) or default_parser_version
    return NormalizedDocument(
        markdown=normalized_markdown,
        blocks=tuple(blocks),
        parser_name=parser_name,
        parser_version=parser_version,
        content_sha256=digest,
    )


def with_blocks(document: NormalizedDocument, blocks: Sequence[ParsedBlock]) -> NormalizedDocument:
    """返回带结构化块的不可变文档副本。"""
    return NormalizedDocument(
        markdown=document.markdown,
        blocks=tuple(blocks),
        parser_name=document.parser_name,
        parser_version=document.parser_version,
        content_sha256=document.content_sha256,
    )


def _normalize_markdown(markdown: str) -> str:
    normalized = markdown.replace("\r\n", "\n").replace("\r", "\n")
    normalized = "\n".join(line.rstrip() for line in normalized.split("\n"))
    normalized = re.sub(r"\n{3,}", "\n\n", normalized).strip()
    return f"{normalized}\n" if normalized else ""


def _normalize_blocks(raw_blocks: object) -> list[ParsedBlock]:
    if not isinstance(raw_blocks, Sequence) or isinstance(raw_blocks, (str, bytes, bytearray)):
        return []

    normalized: list[ParsedBlock] = []
    for index, raw_block in enumerate(raw_blocks):
        if not isinstance(raw_block, Mapping):
            continue
        content = _first_string(raw_block, ("content", "text", "markdown"))
        if not content:
            continue
        block_type = _first_string(raw_block, ("block_type", "type", "kind")) or "paragraph"
        title_path = _title_path(raw_block)
        source = _source_location(raw_block)
        normalized.append(
            ParsedBlock(
                block_id=f"block-{index:04d}",
                order=index,
                block_type=block_type,
                content=content.strip(),
                title_path=title_path,
                source=source,
            )
        )
    return normalized


def _first_string(values: Mapping[str, object], keys: Sequence[str]) -> str | None:
    for key in keys:
        value = values.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _title_path(values: Mapping[str, object]) -> tuple[str, ...]:
    raw_path = values.get("title_path", values.get("heading_path"))
    if isinstance(raw_path, Sequence) and not isinstance(raw_path, (str, bytes, bytearray)):
        return tuple(item.strip() for item in raw_path if isinstance(item, str) and item.strip())
    if isinstance(raw_path, str) and raw_path.strip():
        return tuple(item.strip() for item in raw_path.split(" > ") if item.strip())
    title = _first_string(values, ("title", "heading"))
    return (title,) if title else ()


def _source_location(values: Mapping[str, object]) -> SourceLocation | None:
    page = _integer(values, ("page_number", "page", "page_no"))
    line_start = _integer(values, ("line_start", "start_line"))
    line_end = _integer(values, ("line_end", "end_line"))
    label = _first_string(values, ("source_position", "position", "source"))
    nested = values.get("source_location")
    if isinstance(nested, Mapping):
        page = page or _integer(nested, ("page_number", "page", "page_no"))
        line_start = line_start or _integer(nested, ("line_start", "start_line"))
        line_end = line_end or _integer(nested, ("line_end", "end_line"))
        label = label or _first_string(nested, ("label", "position", "source"))
    if page is None and line_start is None and line_end is None and label is None:
        return None
    return SourceLocation(page_number=page, line_start=line_start, line_end=line_end, label=label)


def _integer(values: Mapping[str, object], keys: Sequence[str]) -> int | None:
    for key in keys:
        value = values.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    return None


def _blocks_to_markdown(blocks: Sequence[ParsedBlock]) -> str:
    lines: list[str] = []
    for block in blocks:
        if block.block_type in {"heading", "title"}:
            level = min(max(len(block.title_path), 1), 6)
            lines.append(f"{'#' * level} {block.content}")
        elif block.block_type == "code":
            lines.extend(("```", block.content, "```"))
        else:
            lines.append(block.content)
        lines.append("")
    return _normalize_markdown("\n".join(lines))
