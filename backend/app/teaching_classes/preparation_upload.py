"""备课上传管理模块：文件验证、存储替换和格式校验。

从 PreparationSessionModule 提取，聚合备课会话文件上传相关的业务逻辑。
"""
from __future__ import annotations

import logging
import uuid
from pathlib import Path

from app.common.errors import BusinessError
from app.teaching_classes.models import FileFormat, UploadStatus

logger = logging.getLogger("course_agent.teaching_classes.preparation_upload")

_SUFFIX_MAP = {
    ".pdf": FileFormat.PDF,
    ".docx": FileFormat.DOCX,
    ".md": FileFormat.MARKDOWN,
    ".markdown": FileFormat.MARKDOWN,
}

_MAX_FILE_SIZE = 20 * 1024 * 1024


def infer_file_format(filename: str) -> FileFormat | None:
    """根据文件名后缀推断文件格式。"""
    return _SUFFIX_MAP.get(Path(filename).suffix.lower())


def validate_file_content(filename: str, content: bytes) -> FileFormat:
    """验证文件格式和签名，返回推断的格式。

    Raises:
        BusinessError: 格式不支持、文件为空、超出大小限制、签名不匹配
    """
    file_format = infer_file_format(filename)
    if file_format is None:
        raise BusinessError(
            status_code=422,
            code="UNSUPPORTED_UPLOAD_FORMAT",
            message="不支持的上传格式，仅支持 pdf、docx、markdown",
        )
    if not content:
        raise BusinessError(
            status_code=422, code="UPLOAD_FILE_EMPTY", message="上传文件不能为空"
        )
    if len(content) > _MAX_FILE_SIZE:
        raise BusinessError(
            status_code=422,
            code="UPLOAD_FILE_TOO_LARGE",
            message="文件大小超过限制，最大支持20MB",
        )

    if file_format is FileFormat.PDF and not content.startswith(b"%PDF-"):
        raise BusinessError(
            status_code=422,
            code="UPLOAD_FILE_SIGNATURE_INVALID",
            message="文件内容与声明格式不一致",
        )
    if file_format is FileFormat.DOCX and not content.startswith(b"PK\x03\x04"):
        raise BusinessError(
            status_code=422,
            code="UPLOAD_FILE_SIGNATURE_INVALID",
            message="文件内容与声明格式不一致",
        )
    if file_format is FileFormat.MARKDOWN and b"\x00" in content:
        raise BusinessError(
            status_code=422,
            code="UPLOAD_FILE_SIGNATURE_INVALID",
            message="文件内容与声明格式不一致",
        )
    return file_format


def generate_storage_key(filename: str) -> str:
    """生成安全的存储键，客户端文件名从不作为服务端路径。"""
    return f"{uuid.uuid4()}{Path(filename).suffix.lower()}"
