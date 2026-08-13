"""课程内容解析 module，收拢受控输入策略与解析 adapter 的选择。"""

import asyncio
import os
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path

from app.document_parsing.markdown import MarkdownParser
from app.document_parsing.mineru import MinerUParser
from app.document_parsing.models import DocumentParser, ParsingError, ParsingResult
from app.teaching_classes.models import FileFormat


def _positive_environment_integer(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError as error:
        raise ParsingError(code="PARSING_CONFIG_INVALID", message=f"{name} 必须是正整数") from error
    if value <= 0:
        raise ParsingError(code="PARSING_CONFIG_INVALID", message=f"{name} 必须是正整数")
    return value


@dataclass(frozen=True)
class ParsingLimits:
    timeout: int = 300
    max_pages: int = 100
    max_paragraphs: int = 1000
    max_output_size: int = 10 * 1024 * 1024
    max_input_size: int = 20 * 1024 * 1024

    @classmethod
    def from_environment(cls) -> "ParsingLimits":
        return cls(
            timeout=_positive_environment_integer("PARSING_TIMEOUT", 300),
            max_pages=_positive_environment_integer("MAX_PAGES", 100),
            max_paragraphs=_positive_environment_integer("MAX_PARAGRAPHS", 1000),
            max_output_size=_positive_environment_integer("MAX_OUTPUT_SIZE", 10 * 1024 * 1024),
        )


ParserFactory = Callable[[], DocumentParser]
AsyncExecutor = Callable[[Awaitable[ParsingResult]], ParsingResult]


class CourseContentParsing:
    """以受控文件和格式为小 interface 产出统一解析结果。"""

    def __init__(
        self,
        *,
        markdown_parser_factory: ParserFactory = MarkdownParser,
        mineru_parser_factory: ParserFactory = MinerUParser,
        async_executor: AsyncExecutor = asyncio.run,
        limits: ParsingLimits | None = None,
    ) -> None:
        self._markdown_parser_factory = markdown_parser_factory
        self._mineru_parser_factory = mineru_parser_factory
        self._async_executor = async_executor
        self._limits = limits or ParsingLimits.from_environment()

    def parse(self, file_path: Path, file_format: FileFormat) -> ParsingResult:
        """在后台运行中执行解析；adapter 的细节不泄露给调用者。"""
        if not file_path.is_file():
            raise ParsingError(code="FILE_NOT_FOUND", message="待解析文件不存在")
        if file_path.stat().st_size > self._limits.max_input_size:
            raise ParsingError(code="FILE_TOO_LARGE", message="文件大小超过 20MB 限制")
        expected_suffix = {
            FileFormat.MARKDOWN: {".md", ".markdown"},
            FileFormat.PDF: {".pdf"},
            FileFormat.DOCX: {".docx"},
        }[file_format]
        if file_path.suffix.lower() not in expected_suffix:
            raise ParsingError(code="FILE_FORMAT_MISMATCH", message="文件扩展名与声明格式不一致")
        parser = (
            self._markdown_parser_factory()
            if file_format is FileFormat.MARKDOWN
            else self._mineru_parser_factory()
        )
        return self._async_executor(
            parser.parse(
                file_path,
                timeout=self._limits.timeout,
                max_pages=self._limits.max_pages,
                max_paragraphs=self._limits.max_paragraphs,
                max_output_size=self._limits.max_output_size,
            )
        )
