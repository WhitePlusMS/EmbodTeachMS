"""文档解析适配层。

提供统一的文档解析接口，支持 PDF、DOCX 和 Markdown 格式的安全解析。
PDF 和 DOCX 通过 MinerU 服务解析，Markdown 使用本地安全文本归一化。
"""

from .models import (
    DocumentParser,
    NormalizedDocument,
    ParsedBlock,
    ParsingResult,
    ParsingError,
    ParsingStatus,
    ParsedParagraph,
    SourceLocation,
)
from .mineru import MinerUParser
from .markdown import MarkdownParser
from .course_content import CourseContentParsing, ParsingLimits
from .normalization import normalize_external_document, normalize_markdown_document

__all__ = [
    "DocumentParser",
    "NormalizedDocument",
    "ParsedBlock",
    "ParsingResult",
    "ParsingError",
    "ParsingStatus",
    "ParsedParagraph",
    "SourceLocation",
    "MinerUParser",
    "MarkdownParser",
    "CourseContentParsing",
    "ParsingLimits",
    "normalize_external_document",
    "normalize_markdown_document",
]
