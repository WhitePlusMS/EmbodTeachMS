"""MinerU 文档解析适配器。

通过 HTTP API 调用 MinerU 服务解析 PDF 和 DOCX 文档。
"""

import asyncio
import json
import logging
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Optional

import httpx

from .models import DocumentParser, ParsedParagraph, ParsingError, ParsingResult, ParsingStatus
from .normalization import normalize_external_document


logger = logging.getLogger("course_agent.document_parsing.mineru")


class MinerUParser(DocumentParser):
    """MinerU 文档解析器"""

    def __init__(self, base_url: Optional[str] = None) -> None:
        """初始化 MinerU 解析器

        Args:
            base_url: MinerU 服务基础 URL，从环境变量 MINERU_BASE_URL 获取
        """
        self.base_url = base_url or os.getenv("MINERU_BASE_URL")
        if not self.base_url:
            raise ParsingError(
                code="MINERU_CONFIG_MISSING",
                message="MinerU 服务未配置，请设置 MINERU_BASE_URL 环境变量"
            )

        # 移除末尾的斜杠
        self.base_url = self.base_url.rstrip("/")

    async def parse(
        self,
        file_path: Path,
        timeout: int = 300,
        max_pages: int = 100,
        max_paragraphs: int = 1000,
        max_output_size: int = 10 * 1024 * 1024,
    ) -> ParsingResult:
        """通过 MinerU 解析 PDF 或 DOCX 文档

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
        # 存在性/大小/格式校验由入口 CourseContentParsing 统一完成，适配器只负责提取
        file_extension = file_path.suffix.lower()
        file_size = file_path.stat().st_size
        logger.info("mineru_parse_started size_bytes=%d timeout_seconds=%d", file_size, timeout)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                # 上传文件到 MinerU
                with open(file_path, "rb") as f:
                    files = {"file": (file_path.name, f, f"application/{file_extension[1:]}")}

                    response = await client.post(
                        f"{self.base_url}/parse",
                        files=files,
                        params={
                            "max_pages": max_pages,
                            "max_blocks": max_paragraphs,
                            "output_format": "json"
                        }
                    )

                # 检查响应状态
                if response.status_code != 200:
                    raise ParsingError(
                        code="MINERU_API_ERROR",
                        message="文档解析服务暂时不可用"
                    )

                # 解析响应
                result_data = response.json()

                # 验证响应结构
                if not isinstance(result_data, Mapping):
                    raise ParsingError(
                        code="MINERU_RESPONSE_INVALID",
                        message="MinerU 返回的响应格式无效"
                    )
                try:
                    normalized_document = normalize_external_document(
                        result_data,
                        parser_name="mineru",
                        default_parser_version="unknown",
                    )
                except ValueError as error:
                    raise ParsingError(
                        code="MINERU_RESPONSE_EMPTY",
                        message="MinerU 未返回可用的 Markdown 内容",
                    ) from error

                paragraphs: list[ParsedParagraph] = []
                current_size = 0
                for block in normalized_document.blocks:
                    if block.block_type == "code":
                        continue
                    block_size = len(block.content.encode("utf-8"))
                    if current_size + block_size > max_output_size or len(paragraphs) >= max_paragraphs:
                        logger.warning("mineru_output_limit_reached max_size=%d", max_output_size)
                        break
                    paragraphs.append(ParsedParagraph(
                        content=block.content,
                        order=len(paragraphs),
                        block_type=block.block_type,
                    ))
                    current_size += block_size

                logger.info(
            "mineru_parse_completed paragraph_count=%d",
                    len(paragraphs),
                )

                return ParsingResult(
                    status=ParsingStatus.COMPLETED,
                    paragraphs=paragraphs,
                    normalized_document=normalized_document,
                )

        except (asyncio.TimeoutError, httpx.TimeoutException):
            logger.warning(
                "mineru_parse_timeout timeout_seconds=%d",
                timeout,
            )
            return ParsingResult(
                status=ParsingStatus.TIMED_OUT,
                paragraphs=[],
                timed_out=True,
                error_message="解析超时"
            )

        except httpx.RequestError as error:
            logger.error("mineru_connection_error error_type=%s", type(error).__name__)
            raise ParsingError(
                code="MINERU_CONNECTION_ERROR",
                message="文档解析服务暂时不可用"
            ) from error

        except json.JSONDecodeError as error:
            logger.error("mineru_response_json_error")
            raise ParsingError(
                code="MINERU_RESPONSE_JSON_ERROR",
                message="MinerU 返回的 JSON 响应格式错误"
            ) from error

        except ParsingError:
            raise
        except Exception as error:
            logger.error("mineru_unexpected_error error_type=%s", type(error).__name__)
            raise ParsingError(
                code="MINERU_UNEXPECTED_ERROR",
                message="文档解析失败"
            ) from error
