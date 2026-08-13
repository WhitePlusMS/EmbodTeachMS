"""文档解析模型定义。

定义统一的解析接口、结果模型和错误类型。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class SourceLocation:
    """结构化内容在原始文档中的可追踪位置。"""

    page_number: int | None = None
    line_start: int | None = None
    line_end: int | None = None
    label: str | None = None


@dataclass(frozen=True)
class ParsedBlock:
    """Markdown-first 文档中的一个结构化语义块。"""

    block_id: str
    order: int
    block_type: str
    content: str
    title_path: tuple[str, ...] = ()
    source: SourceLocation | None = None
    heading_level: int | None = None


@dataclass(frozen=True)
class NormalizedDocument:
    """解析适配器统一产出的规范化文档。"""

    markdown: str
    blocks: tuple[ParsedBlock, ...]
    parser_name: str
    parser_version: str
    content_sha256: str


class ParsingStatus(str, Enum):
    """解析状态枚举"""
    NOT_STARTED = "not_started"
    PARSING = "parsing"
    COMPLETED = "completed"
    TIMED_OUT = "timed_out"
    FAILED = "failed"


@dataclass
class ParsedParagraph:
    """解析后的段落模型"""
    content: str
    """段落文本内容"""
    order: int
    """阅读顺序（从0开始）"""
    block_type: str
    """块类型（标题、正文、列表、表格等）"""


@dataclass
class ParsingResult:
    """解析结果模型"""
    status: ParsingStatus
    """解析状态"""
    paragraphs: list[ParsedParagraph]
    """解析出的段落列表"""
    error_message: Optional[str] = None
    """错误信息（仅在失败时设置）"""
    timed_out: bool = False
    """是否超时"""
    normalized_document: NormalizedDocument | None = None
    """Markdown-first 结构化输出；旧调用方只读取 paragraphs。"""


@dataclass
class ParsingError(Exception):
    """解析错误"""
    code: str
    """错误代码"""
    message: str
    """错误信息"""

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


class DocumentParser(ABC):
    """文档解析器抽象基类"""

    @abstractmethod
    async def parse(
        self,
        file_path: Path,
        timeout: int = 300,
        max_pages: int = 100,
        max_paragraphs: int = 1000,
        max_output_size: int = 10 * 1024 * 1024,  # 10MB
    ) -> ParsingResult:
        """解析文档文件

        Args:
            file_path: 要解析的文件路径
            timeout: 解析超时时间（秒）
            max_pages: 最大页数限制
            max_paragraphs: 最大段落数限制
            max_output_size: 最大输出大小限制（字节）

        Returns:
            ParsingResult: 解析结果

        Raises:
            ParsingError: 解析过程中发生错误
        """
        pass
