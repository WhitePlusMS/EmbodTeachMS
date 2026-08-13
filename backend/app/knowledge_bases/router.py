"""知识库路由：通过 _deps 共享 DI，无内联业务逻辑。

所有业务逻辑下沉到 service.py 的 ensure_document_parsed、import_documents_and_parse 等方法。
"""
import logging
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, status
from fastapi import Request as FastAPIRequest

from app.common.api_response import ApiResponse
from app.common.errors import BusinessError
from app.common.responses import documented_error, success_response
from app.document_parsing import MarkdownParser, ParsingError
from app.knowledge_bases._deps import KnowledgeBaseServiceDep, TeacherDep
from app.knowledge_bases.models import (
    CopyKnowledgeBaseRequest,
    CreateKnowledgeBaseRequest,
    ImportKnowledgeBaseDocumentsRequest,
    KnowledgeBaseImportView,
    KnowledgeBaseIndexStatusView,
    KnowledgeBaseListView,
    KnowledgeBasePublicationView,
    KnowledgeBaseSearchView,
    KnowledgeBaseSearchRequest,
    KnowledgeBaseSegmentListView,
    KnowledgeBaseSegmentPreviewRequest,
    KnowledgeBaseSegmentPreviewView,
    KnowledgeBaseSegmentRebuildView,
    KnowledgeBaseSettingsView,
    KnowledgeBaseView,
    KnowledgeBaseDocumentView,
    KnowledgeBaseDocumentListView,
    KnowledgeBaseRetrievalTestRequest,
    UpdateKnowledgeBaseDocumentRequest,
    UpdateKnowledgeBaseRequest,
    UpdateKnowledgeBaseSettingsRequest,
)

router = APIRouter(prefix="/api/knowledge-bases", tags=["knowledge-bases"])
logger = logging.getLogger("course_agent.knowledge_bases.router")


# ── 知识库 CRUD ──────────────────────────────────────────────────


@router.post(
    "",
    response_model=ApiResponse[KnowledgeBaseView],
    status_code=status.HTTP_201_CREATED,
    responses={403: documented_error("只有教师可以管理课件知识库"), 409: documented_error("知识库名称已存在"), 422: documented_error("请求参数不正确")},
)
def create_knowledge_base(
    request: FastAPIRequest,
    body: CreateKnowledgeBaseRequest,
    teacher: TeacherDep,
    service: KnowledgeBaseServiceDep,
) -> ApiResponse[KnowledgeBaseView]:
    knowledge_base = service.create(body, teacher)
    return success_response(request, code="KNOWLEDGE_BASE_CREATED", message="知识库创建成功", data=knowledge_base)


@router.get(
    "",
    response_model=ApiResponse[KnowledgeBaseListView],
    responses={403: documented_error("只有教师可以查看课件知识库")},
)
def list_knowledge_bases(
    request: FastAPIRequest,
    teacher: TeacherDep,
    service: KnowledgeBaseServiceDep,
) -> ApiResponse[KnowledgeBaseListView]:
    knowledge_bases = service.list_for_teacher(teacher)
    return success_response(request, code="KNOWLEDGE_BASES_LISTED", message="知识库列表获取成功", data=knowledge_bases)


@router.get(
    "/{knowledge_base_id}",
    response_model=ApiResponse[KnowledgeBaseView],
    responses={403: documented_error("只有教师可以查看课件知识库"), 404: documented_error("知识库不存在")},
)
def get_knowledge_base(
    request: FastAPIRequest,
    knowledge_base_id: str,
    teacher: TeacherDep,
    service: KnowledgeBaseServiceDep,
) -> ApiResponse[KnowledgeBaseView]:
    knowledge_base = service.get(knowledge_base_id, teacher)
    return success_response(request, code="KNOWLEDGE_BASE_FETCHED", message="知识库获取成功", data=knowledge_base)


@router.patch(
    "/{knowledge_base_id}",
    response_model=ApiResponse[KnowledgeBaseView],
    responses={400: documented_error("至少提供一个需要更新的字段"), 403: documented_error("只有教师可以更新课件知识库"), 404: documented_error("知识库不存在"), 409: documented_error("知识库名称已存在")},
)
def update_knowledge_base(
    request: FastAPIRequest,
    knowledge_base_id: str,
    body: UpdateKnowledgeBaseRequest,
    teacher: TeacherDep,
    service: KnowledgeBaseServiceDep,
) -> ApiResponse[KnowledgeBaseView]:
    knowledge_base = service.update(knowledge_base_id, body, teacher)
    return success_response(request, code="KNOWLEDGE_BASE_UPDATED", message="知识库更新成功", data=knowledge_base)


@router.post(
    "/{knowledge_base_id}/archive",
    response_model=ApiResponse[KnowledgeBaseView],
    responses={403: documented_error("只有教师可以归档课件知识库"), 404: documented_error("知识库不存在")},
)
def archive_knowledge_base(
    request: FastAPIRequest,
    knowledge_base_id: str,
    teacher: TeacherDep,
    service: KnowledgeBaseServiceDep,
) -> ApiResponse[KnowledgeBaseView]:
    knowledge_base = service.archive(knowledge_base_id, teacher)
    return success_response(request, code="KNOWLEDGE_BASE_ARCHIVED", message="知识库已归档", data=knowledge_base)


@router.delete(
    "/{knowledge_base_id}",
    response_model=ApiResponse[None],
    responses={403: documented_error("只有教师可以删除课件知识库"), 404: documented_error("知识库不存在"), 409: documented_error("知识库已有教学班副本，不能删除来源知识库")},
)
def delete_knowledge_base(
    request: FastAPIRequest,
    knowledge_base_id: str,
    teacher: TeacherDep,
    service: KnowledgeBaseServiceDep,
) -> ApiResponse[None]:
    service.delete(knowledge_base_id, teacher)
    return success_response(request, code="KNOWLEDGE_BASE_DELETED", message="知识库删除成功", data=None)


# ── 复制 / 导入 / 发布 ──────────────────────────────────────────


@router.post(
    "/{knowledge_base_id}/copies",
    response_model=ApiResponse[KnowledgeBaseView],
    status_code=status.HTTP_201_CREATED,
    responses={403: documented_error("只有教师可以复制课件知识库"), 404: documented_error("知识库或教学班不存在"), 409: documented_error("知识库不能复制到该教学班"), 422: documented_error("请求参数不正确")},
)
def copy_knowledge_base_to_class(
    request: FastAPIRequest,
    knowledge_base_id: str,
    body: CopyKnowledgeBaseRequest,
    teacher: TeacherDep,
    service: KnowledgeBaseServiceDep,
) -> ApiResponse[KnowledgeBaseView]:
    knowledge_base = service.copy_to_class(knowledge_base_id, body, teacher)
    return success_response(request, code="KNOWLEDGE_BASE_COPIED", message="知识库已复制到教学班", data=knowledge_base)


@router.post(
    "/imports",
    response_model=ApiResponse[KnowledgeBaseImportView],
    status_code=status.HTTP_201_CREATED,
    responses={403: documented_error("只有教师可以导入知识库文档"), 404: documented_error("来源文档或教学班不存在"), 409: documented_error("知识库文档导入失败")},
)
def import_knowledge_base_documents(
    request: FastAPIRequest,
    body: ImportKnowledgeBaseDocumentsRequest,
    teacher: TeacherDep,
    service: KnowledgeBaseServiceDep,
) -> ApiResponse[KnowledgeBaseImportView]:
    """导入知识库文档并在服务层完成解析和索引，出错自动回滚。"""
    imported = service.import_documents_and_parse(body, teacher)
    return success_response(request, code="KNOWLEDGE_BASE_DOCUMENTS_IMPORTED", message="知识库文档已导入并完成目标端解析索引", data=imported)


@router.post(
    "/{knowledge_base_id}/publish",
    response_model=ApiResponse[KnowledgeBasePublicationView],
    status_code=status.HTTP_201_CREATED,
    responses={403: documented_error("没有权限发布知识库"), 404: documented_error("知识库不存在"), 409: documented_error("知识库尚未准备好发布")},
)
def publish_knowledge_base(
    request: FastAPIRequest,
    knowledge_base_id: str,
    teacher: TeacherDep,
    service: KnowledgeBaseServiceDep,
) -> ApiResponse[KnowledgeBasePublicationView]:
    publication = service.publish_to_class(knowledge_base_id, teacher)
    return success_response(request, code="KNOWLEDGE_BASE_PUBLISHED", message="知识库已发布为课程内容快照", data=publication)


# ── 搜索 / 检索 ──────────────────────────────────────────────────


@router.post(
    "/{knowledge_base_id}/search",
    response_model=ApiResponse[KnowledgeBaseSearchView],
    responses={403: documented_error("只有教师可以检索课件知识库"), 404: documented_error("知识库不存在")},
)
def search_knowledge_base(
    request: FastAPIRequest,
    knowledge_base_id: str,
    body: KnowledgeBaseSearchRequest,
    teacher: TeacherDep,
    service: KnowledgeBaseServiceDep,
) -> ApiResponse[KnowledgeBaseSearchView]:
    result = service.search_for_knowledge_base(knowledge_base_id, body.query, body.limit, teacher)
    return success_response(request, code="KNOWLEDGE_BASE_SEARCHED", message="知识库检索完成", data=result)


@router.post(
    "/{knowledge_base_id}/retrieval-tests",
    response_model=ApiResponse[KnowledgeBaseSearchView],
    responses={403: documented_error("只有教师可以测试知识库召回"), 404: documented_error("知识库不存在")},
)
def test_knowledge_base_retrieval(
    request: FastAPIRequest,
    knowledge_base_id: str,
    body: KnowledgeBaseRetrievalTestRequest,
    teacher: TeacherDep,
    service: KnowledgeBaseServiceDep,
) -> ApiResponse[KnowledgeBaseSearchView]:
    result = service.retrieval_test(knowledge_base_id, body, teacher)
    return success_response(request, code="KNOWLEDGE_BASE_RETRIEVAL_TESTED", message="知识库召回测试完成", data=result)


@router.get(
    "/{knowledge_base_id}/index-status",
    response_model=ApiResponse[KnowledgeBaseIndexStatusView],
    responses={403: documented_error("没有权限查看索引状态"), 404: documented_error("知识库不存在")},
)
def get_knowledge_base_index_status(
    request: FastAPIRequest,
    knowledge_base_id: str,
    teacher: TeacherDep,
    service: KnowledgeBaseServiceDep,
) -> ApiResponse[KnowledgeBaseIndexStatusView]:
    status_view = service.get_index_status(knowledge_base_id, teacher)
    return success_response(request, code="KNOWLEDGE_BASE_INDEX_STATUS_FETCHED", message="索引状态获取成功", data=status_view)


# ── 文档管理 ─────────────────────────────────────────────────────


@router.post(
    "/{knowledge_base_id}/documents",
    response_model=ApiResponse[KnowledgeBaseDocumentView],
    status_code=status.HTTP_201_CREATED,
    responses={400: documented_error("文件为空或格式不支持"), 403: documented_error("没有权限修改知识库"), 422: documented_error("文档处理失败")},
)
async def upload_knowledge_base_document(
    request: FastAPIRequest,
    knowledge_base_id: str,
    teacher: TeacherDep,
    service: KnowledgeBaseServiceDep,
    file: UploadFile = File(...),
) -> ApiResponse[KnowledgeBaseDocumentView]:
    """上传并保存 Markdown 原文件，文档可直接进入分段预览。"""
    filename = Path(file.filename or "").name
    suffix = Path(filename).suffix.lower()
    if suffix not in {".md", ".markdown"}:
        raise BusinessError(status_code=400, code="FILE_FORMAT_UNSUPPORTED", message="仅支持 Markdown 文件（.md、.markdown）")
    content = await file.read()
    if not content:
        raise BusinessError(status_code=400, code="FILE_EMPTY", message="上传文件不能为空")
    if len(content) > 20 * 1024 * 1024:
        raise BusinessError(status_code=400, code="FILE_TOO_LARGE", message="文件大小超过 20MB 限制")
    document = service.save_uploaded_document(knowledge_base_id, filename, content, teacher)
    return success_response(request, code="KNOWLEDGE_BASE_DOCUMENT_UPLOADED", message="课件上传成功，可直接查看分段", data=document)


@router.get(
    "/{knowledge_base_id}/documents",
    response_model=ApiResponse[KnowledgeBaseDocumentListView],
    responses={403: documented_error("没有权限查看知识库文档"), 404: documented_error("知识库不存在")},
)
def list_knowledge_base_documents(
    request: FastAPIRequest,
    knowledge_base_id: str,
    teacher: TeacherDep,
    service: KnowledgeBaseServiceDep,
) -> ApiResponse[KnowledgeBaseDocumentListView]:
    documents = service.list_documents(knowledge_base_id, teacher)
    return success_response(request, code="KNOWLEDGE_BASE_DOCUMENTS_LISTED", message="知识库文档列表获取成功", data=documents)


@router.get(
    "/{knowledge_base_id}/documents/{document_id}",
    response_model=ApiResponse[KnowledgeBaseDocumentView],
    responses={403: documented_error("没有权限查看知识库文档"), 404: documented_error("文档不存在")},
)
def get_knowledge_base_document(
    request: FastAPIRequest,
    knowledge_base_id: str,
    document_id: str,
    teacher: TeacherDep,
    service: KnowledgeBaseServiceDep,
) -> ApiResponse[KnowledgeBaseDocumentView]:
    document = service.get_document(knowledge_base_id, document_id, teacher)
    return success_response(request, code="KNOWLEDGE_BASE_DOCUMENT_FETCHED", message="知识库文档获取成功", data=document)


@router.patch(
    "/{knowledge_base_id}/documents/{document_id}",
    response_model=ApiResponse[KnowledgeBaseDocumentView],
    responses={400: documented_error("文档修改内容不正确"), 403: documented_error("没有权限修改知识库文档"), 404: documented_error("文档不存在")},
)
def update_knowledge_base_document(
    request: FastAPIRequest,
    knowledge_base_id: str,
    document_id: str,
    body: UpdateKnowledgeBaseDocumentRequest,
    teacher: TeacherDep,
    service: KnowledgeBaseServiceDep,
) -> ApiResponse[KnowledgeBaseDocumentView]:
    document = service.update_document(knowledge_base_id, document_id, body, teacher)
    return success_response(request, code="KNOWLEDGE_BASE_DOCUMENT_UPDATED", message="知识库文档更新成功", data=document)


@router.post(
    "/{knowledge_base_id}/documents/{document_id}/replace",
    response_model=ApiResponse[KnowledgeBaseDocumentView],
    responses={400: documented_error("文件为空或格式不支持"), 403: documented_error("没有权限修改知识库文档"), 404: documented_error("文档不存在")},
)
async def replace_knowledge_base_document(
    request: FastAPIRequest,
    knowledge_base_id: str,
    document_id: str,
    teacher: TeacherDep,
    service: KnowledgeBaseServiceDep,
    file: UploadFile = File(...),
) -> ApiResponse[KnowledgeBaseDocumentView]:
    filename = Path(file.filename or "").name
    if Path(filename).suffix.lower() not in {".md", ".markdown"}:
        raise BusinessError(status_code=400, code="FILE_FORMAT_UNSUPPORTED", message="仅支持 Markdown 文件（.md、.markdown）")
    content = await file.read()
    document = service.replace_document_source(knowledge_base_id, document_id, filename, content, teacher)
    return success_response(request, code="KNOWLEDGE_BASE_DOCUMENT_REPLACED", message="知识库文档已替换，请重新构建索引", data=document)


@router.delete(
    "/{knowledge_base_id}/documents/{document_id}",
    response_model=ApiResponse[None],
    responses={403: documented_error("没有权限删除知识库文档"), 404: documented_error("文档不存在")},
)
def delete_knowledge_base_document(
    request: FastAPIRequest,
    knowledge_base_id: str,
    document_id: str,
    teacher: TeacherDep,
    service: KnowledgeBaseServiceDep,
) -> ApiResponse[None]:
    service.delete_document(knowledge_base_id, document_id, teacher)
    return success_response(request, code="KNOWLEDGE_BASE_DOCUMENT_DELETED", message="知识库文档删除成功", data=None)


# ── 设置 ─────────────────────────────────────────────────────────


@router.get(
    "/{knowledge_base_id}/settings",
    response_model=ApiResponse[KnowledgeBaseSettingsView],
    responses={403: documented_error("没有权限查看知识库设置"), 404: documented_error("知识库不存在")},
)
def get_knowledge_base_settings(
    request: FastAPIRequest,
    knowledge_base_id: str,
    teacher: TeacherDep,
    service: KnowledgeBaseServiceDep,
) -> ApiResponse[KnowledgeBaseSettingsView]:
    settings_view = service.get_settings(knowledge_base_id, teacher)
    return success_response(request, code="KNOWLEDGE_BASE_SETTINGS_FETCHED", message="知识库设置获取成功", data=settings_view)


@router.patch(
    "/{knowledge_base_id}/settings",
    response_model=ApiResponse[KnowledgeBaseSettingsView],
    responses={400: documented_error("分段参数不正确"), 403: documented_error("没有权限修改知识库设置"), 404: documented_error("知识库不存在")},
)
def update_knowledge_base_settings(
    request: FastAPIRequest,
    knowledge_base_id: str,
    body: UpdateKnowledgeBaseSettingsRequest,
    teacher: TeacherDep,
    service: KnowledgeBaseServiceDep,
) -> ApiResponse[KnowledgeBaseSettingsView]:
    settings_view = service.update_settings(knowledge_base_id, body, teacher)
    return success_response(request, code="KNOWLEDGE_BASE_SETTINGS_UPDATED", message="知识库分段设置已保存，请重建索引", data=settings_view)


# ── 分段管理 ─────────────────────────────────────────────────────


@router.post(
    "/{knowledge_base_id}/segments/preview",
    response_model=ApiResponse[KnowledgeBaseSegmentPreviewView],
    responses={403: documented_error("没有权限预览知识库分段"), 404: documented_error("文档不存在"), 409: documented_error("文档尚未准备好")},
)
def preview_knowledge_base_segments(
    request: FastAPIRequest,
    knowledge_base_id: str,
    body: KnowledgeBaseSegmentPreviewRequest,
    teacher: TeacherDep,
    service: KnowledgeBaseServiceDep,
) -> ApiResponse[KnowledgeBaseSegmentPreviewView]:
    """预览分段前确保文档已解析。"""
    service.ensure_document_parsed(knowledge_base_id, body.document_id, teacher)
    preview = service.preview_segments(knowledge_base_id, body, teacher)
    return success_response(request, code="KNOWLEDGE_BASE_SEGMENTS_PREVIEWED", message="分段预览生成成功", data=preview)


@router.post(
    "/{knowledge_base_id}/segments/rebuild",
    response_model=ApiResponse[KnowledgeBaseSegmentRebuildView],
    responses={403: documented_error("没有权限重建知识库分段"), 404: documented_error("文档不存在"), 409: documented_error("文档尚未准备好")},
)
def rebuild_knowledge_base_segments(
    request: FastAPIRequest,
    knowledge_base_id: str,
    body: KnowledgeBaseSegmentPreviewRequest,
    teacher: TeacherDep,
    service: KnowledgeBaseServiceDep,
) -> ApiResponse[KnowledgeBaseSegmentRebuildView]:
    """重建分段前确保文档已解析。"""
    service.ensure_document_parsed(knowledge_base_id, body.document_id, teacher)
    rebuilt = service.rebuild_segments(knowledge_base_id, body, teacher)
    return success_response(request, code="KNOWLEDGE_BASE_SEGMENTS_REBUILT", message="分段和关键词索引已重建", data=rebuilt)


@router.get(
    "/{knowledge_base_id}/segments",
    response_model=ApiResponse[KnowledgeBaseSegmentListView],
    responses={403: documented_error("没有权限查看知识库分段"), 404: documented_error("知识库不存在")},
)
def list_knowledge_base_segments(
    request: FastAPIRequest,
    knowledge_base_id: str,
    teacher: TeacherDep,
    service: KnowledgeBaseServiceDep,
) -> ApiResponse[KnowledgeBaseSegmentListView]:
    segments = service.list_segments(knowledge_base_id, teacher)
    return success_response(request, code="KNOWLEDGE_BASE_SEGMENTS_LISTED", message="知识库分段列表获取成功", data=segments)


# ── 重试 ─────────────────────────────────────────────────────────


@router.post(
    "/documents/{document_id}/retry",
    response_model=ApiResponse[KnowledgeBaseDocumentView],
    status_code=status.HTTP_200_OK,
    responses={404: documented_error("失败文档不存在"), 422: documented_error("文档解析失败")},
)
async def retry_knowledge_base_document(
    request: FastAPIRequest,
    document_id: str,
    teacher: TeacherDep,
    service: KnowledgeBaseServiceDep,
) -> ApiResponse[KnowledgeBaseDocumentView]:
    """重试失败文档：重新解析并更新文档状态。"""
    knowledge_base_id, filename, file_format, source_path = service.get_failed_document_source(document_id, teacher)
    if not source_path.is_file():
        raise BusinessError(status_code=422, code="DOCUMENT_SOURCE_MISSING", message="原始输入文件已不存在，无法重试")
    expected_version: int | None = None
    try:
        expected_version = service.mark_document_parsing(document_id, teacher)
        parser = MarkdownParser()
        result = await parser.parse(source_path)
        if result.normalized_document is None or not result.normalized_document.markdown.strip():
            raise ParsingError(code="MARKDOWN_EMPTY", message="Markdown 文件没有可构建的内容")
        document = service.complete_uploaded_document(
            document_id, result.normalized_document, teacher, expected_version=expected_version,
        )
        return success_response(request, code="KNOWLEDGE_BASE_DOCUMENT_RETRIED", message="文档重试解析成功", data=document)
    except BusinessError:
        raise
    except ParsingError as error:
        if expected_version is None:
            raise
        failed_document = service.mark_document_failed(document_id, error.code, error.message, teacher, expected_version=expected_version)
        return success_response(request, code="KNOWLEDGE_BASE_DOCUMENT_PARSE_FAILED", message=error.message, data=failed_document)
    except OSError:
        if expected_version is None:
            raise
        failed_document = service.mark_document_failed(document_id, "DOCUMENT_READ_FAILED", "Markdown 文件读取失败", teacher, expected_version=expected_version)
        return success_response(request, code="KNOWLEDGE_BASE_DOCUMENT_PARSE_FAILED", message="Markdown 文件读取失败", data=failed_document)
    except Exception:
        logger.exception("knowledge_base_retry_failed document_id=%s", document_id)
        if expected_version is None:
            raise
        failed_document = service.mark_document_failed(document_id, "KNOWLEDGE_BASE_PARSE_FAILED", "文档解析失败，请稍后重试", teacher, expected_version=expected_version)
        return success_response(request, code="KNOWLEDGE_BASE_DOCUMENT_PARSE_FAILED", message="文档解析失败，请稍后重试", data=failed_document)
