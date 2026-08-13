"""Markdown 文档解析适配器。

使用安全的文本归一化处理 Markdown 文档，不执行 HTML、代码块或外部资源。
"""

import logging
import re
from pathlib import Path

from .models import (
    DocumentParser,
    NormalizedDocument,
    ParsedBlock,
    ParsedParagraph,
    ParsingError,
    ParsingResult,
    ParsingStatus,
    SourceLocation,
)
from .normalization import normalize_markdown_document, with_blocks


logger = logging.getLogger("course_agent.document_parsing.markdown")


class MarkdownParser(DocumentParser):
    """Markdown 文档解析器"""

    def __init__(self) -> None:
        """初始化 Markdown 解析器"""
        # 正则表达式用于安全提取 Markdown 文本内容
        self._heading_pattern = re.compile(r'^#{1,6}\s+(.+)$', re.MULTILINE)
        self._list_pattern = re.compile(r'^[\*\-\+]\s+(.+)$', re.MULTILINE)
        self._code_block_pattern = re.compile(r'```[^`]*```', re.DOTALL)
        self._inline_code_pattern = re.compile(r'`[^`]+`')
        self._html_pattern = re.compile(r'<[^>]+>')
        self._link_pattern = re.compile(r'\[([^\]]+)\]\([^)]+\)')

    async def parse(
        self,
        file_path: Path,
        timeout: int = 300,
        max_pages: int = 100,
        max_paragraphs: int = 1000,
        max_output_size: int = 10 * 1024 * 1024,
    ) -> ParsingResult:
        """安全解析 Markdown 文档（async 接口，委派给同步实现）。"""
        return self._parse_sync(file_path, max_paragraphs, max_output_size)

    def parse_sync(
        self,
        file_path: Path,
        timeout: int = 300,
        max_pages: int = 100,
        max_paragraphs: int = 1000,
        max_output_size: int = 10 * 1024 * 1024,
    ) -> ParsingResult:
        """同步解析 Markdown 文档，供同步上下文直接使用（无需 asyncio.run）。"""
        return self._parse_sync(file_path, max_paragraphs, max_output_size)

    def _parse_sync(
        self,
        file_path: Path,
        max_paragraphs: int,
        max_output_size: int,
    ) -> ParsingResult:
        """同步解析核心实现。"""
        # 存在性/大小/格式校验由入口 CourseContentParsing 统一完成，适配器只负责提取
        file_size = file_path.stat().st_size
        logger.info("markdown_parse_started size_bytes=%d", file_size)

        try:
            # 读取文件内容（UTF-8编码）
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            normalized_document = normalize_markdown_document(
                content,
                parser_name="markdown",
                parser_version="local-v2",
            )
            blocks = self._extract_blocks(content, max_output_size)
            normalized_document = with_blocks(normalized_document, blocks)
            paragraphs = self._paragraphs_from_blocks(blocks, max_paragraphs, max_output_size)

            logger.info(
            "markdown_parse_completed paragraph_count=%d",
                len(paragraphs),
            )

            return ParsingResult(
                status=ParsingStatus.COMPLETED,
                paragraphs=paragraphs,
                normalized_document=normalized_document,
            )

        except UnicodeDecodeError as error:
            logger.error("markdown_unicode_error")
            raise ParsingError(
                code="MARKDOWN_DECODE_ERROR",
                message="Markdown 文件编码错误，无法读取"
            ) from error

        except ParsingError:
            raise
        except Exception as error:
            logger.error("markdown_unexpected_error error_type=%s", type(error).__name__)
            raise ParsingError(
                code="MARKDOWN_UNEXPECTED_ERROR",
                message="Markdown 文档解析失败"
            ) from error

    def _extract_blocks(self, content: str, max_output_size: int) -> list[ParsedBlock]:
        """按 Markdown 结构提取标题、段落、列表、表格、代码和公式块。"""
        lines = content.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        blocks: list[ParsedBlock] = []
        current_lines: list[str] = []
        current_start = 1
        headings: list[tuple[int, str]] = []
        index = 0

        def append_block(
            block_type: str,
            text: str,
            start: int,
            end: int,
            path: tuple[str, ...],
            heading_level: int | None = None,
        ) -> bool:
            nonlocal index
            normalized_text = text if block_type == "code" else self._normalize_text(text)
            if not normalized_text:
                return True
            projected_size = sum(
                len(block.content.encode("utf-8")) for block in blocks
            ) + len(normalized_text.encode("utf-8"))
            if projected_size > max_output_size:
                return False
            blocks.append(
                ParsedBlock(
                    block_id=f"block-{index:04d}",
                    order=index,
                    block_type=block_type,
                    content=normalized_text,
                    title_path=path,
                    source=SourceLocation(line_start=start, line_end=end),
                    heading_level=heading_level,
                )
            )
            index += 1
            return True

        def flush_paragraph(end: int) -> bool:
            nonlocal current_lines
            if not current_lines:
                return True
            path = tuple(title for _, title in headings)
            result = append_block("paragraph", " ".join(current_lines), current_start, end, path)
            current_lines = []
            return result

        line_number = 0
        while line_number < len(lines):
            raw_line = lines[line_number]
            line = raw_line.strip()
            line_number += 1
            if not line:
                if not flush_paragraph(line_number - 1):
                    break
                continue

            fence = re.match(r"^(```+|~~~+)(.*)$", line)
            if fence:
                if not flush_paragraph(line_number - 1):
                    break
                marker = fence.group(1)
                code_lines: list[str] = []
                code_start = line_number
                while line_number < len(lines) and not lines[line_number].strip().startswith(marker):
                    code_lines.append(lines[line_number])
                    line_number += 1
                code_end = line_number + 1 if line_number < len(lines) else line_number
                if line_number < len(lines):
                    line_number += 1
                if not append_block("code", "\n".join(code_lines), code_start, code_end, tuple(title for _, title in headings)):
                    break
                continue

            heading = self._heading_pattern.match(line)
            if heading:
                if not flush_paragraph(line_number - 1):
                    break
                level = len(line) - len(line.lstrip("#"))
                title = self._normalize_text(heading.group(1))
                headings = [(existing_level, value) for existing_level, value in headings if existing_level < level]
                headings.append((level, title))
                if not append_block(
                    "heading",
                    title,
                    line_number,
                    line_number,
                    tuple(value for _, value in headings),
                    heading_level=level,
                ):
                    break
                continue

            if self._is_table_start(lines, line_number - 1):
                if not flush_paragraph(line_number - 1):
                    break
                table_start = line_number
                table_lines = [raw_line]
                while line_number < len(lines) and lines[line_number].strip() and "|" in lines[line_number]:
                    table_lines.append(lines[line_number])
                    line_number += 1
                if not append_block("table", "\n".join(table_lines), table_start, line_number, tuple(title for _, title in headings)):
                    break
                continue

            list_item = self._list_pattern.match(line)
            if list_item:
                if not flush_paragraph(line_number - 1):
                    break
                if not append_block("list", list_item.group(1), line_number, line_number, tuple(title for _, title in headings)):
                    break
                continue

            if line.startswith("$$") or line.startswith(r"\\["):
                if not flush_paragraph(line_number - 1):
                    break
                if not append_block("formula", raw_line, line_number, line_number, tuple(title for _, title in headings)):
                    break
                continue

            if not current_lines:
                current_start = line_number
            current_lines.append(line)

        if current_lines:
            flush_paragraph(len(lines))
        return blocks

    @staticmethod
    def _is_table_start(lines: list[str], index: int) -> bool:
        return (
            index + 1 < len(lines)
            and "|" in lines[index]
            and bool(re.match(r"^\s*\|?\s*:?-{3,}", lines[index + 1]))
        )

    @staticmethod
    def _paragraphs_from_blocks(
        blocks: list[ParsedBlock],
        max_paragraphs: int,
        max_output_size: int,
    ) -> list[ParsedParagraph]:
        """将 ParsedBlock 列表转换为 ParsedParagraph 列表。"""
        paragraphs: list[ParsedParagraph] = []
        current_size = 0
        for block in blocks:
            if block.block_type == "code":
                continue
            block_size = len(block.content.encode("utf-8"))
            if current_size + block_size > max_output_size or len(paragraphs) >= max_paragraphs:
                break
            paragraphs.append(
                ParsedParagraph(
                    content=block.content,
                    order=len(paragraphs),
                    block_type=block.block_type,
                )
            )
            current_size += block_size
        return paragraphs

    def _normalize_text(self, text: str) -> str:
        """归一化文本内容

        Args:
            text: 原始文本

        Returns:
            str: 归一化后的文本
        """
        # 移除内联代码标记
        text = self._inline_code_pattern.sub(
            lambda m: m.group(0)[1:-1],  # 移除反引号，保留内容
            text
        )

        # 移除 HTML 标签（不执行）
        text = self._html_pattern.sub("", text)

        # 移除链接标记，保留链接文本
        text = self._link_pattern.sub(r"\1", text)

        # 移除多余空白字符
        text = re.sub(r'\s+', ' ', text).strip()

        return text
