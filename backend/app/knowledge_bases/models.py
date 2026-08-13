"""知识库文档领域模型。"""

from dataclasses import dataclass
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel


class CamelCaseModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class KnowledgeBaseKind(str, Enum):
    REUSABLE = "reusable"
    CLASS_COPY = "class_copy"


class KnowledgeBaseStatus(str, Enum):
    DRAFT = "draft"
    AVAILABLE = "available"
    ARCHIVED = "archived"


class CreateKnowledgeBaseRequest(CamelCaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)


class UpdateKnowledgeBaseRequest(CamelCaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)


class CopyKnowledgeBaseRequest(CamelCaseModel):
    target_class_id: str = Field(min_length=1)
    name: str | None = Field(default=None, min_length=1, max_length=120)


class KnowledgeBaseImportItem(CamelCaseModel):
    source_knowledge_base_id: str = Field(min_length=1)
    document_ids: list[str] = Field(min_length=1, max_length=100)


class ImportKnowledgeBaseDocumentsRequest(CamelCaseModel):
    target_class_id: str = Field(min_length=1)
    items: list[KnowledgeBaseImportItem] = Field(min_length=1, max_length=100)
    conflict_strategy: Literal["skip", "replace", "copy"] = "skip"


class KnowledgeBaseView(CamelCaseModel):
    id: str
    owner_teacher_id: str
    class_id: str | None
    source_knowledge_base_id: str | None
    kind: KnowledgeBaseKind
    name: str
    description: str
    status: KnowledgeBaseStatus
    source_version: int
    document_count: int
    archived_at: int | None
    created_at: int
    updated_at: int


class KnowledgeBaseListView(CamelCaseModel):
    items: list[KnowledgeBaseView]


class KnowledgeBaseImportView(CamelCaseModel):
    target_knowledge_base: KnowledgeBaseView
    imported_documents: list["KnowledgeBaseDocumentView"]
    skipped_document_ids: list[str]


class KnowledgeBaseDocumentView(CamelCaseModel):
    id: str
    knowledge_base_id: str
    source_document_id: str | None
    title: str
    original_filename: str
    file_format: Literal["pdf", "docx", "markdown"]
    parse_status: Literal["not_started", "parsing", "completed", "failed"]
    error_code: str | None
    error_message: str | None
    parser_name: str | None
    parser_version: str | None
    created_at: int
    updated_at: int
    version: int = 1
    content_hash: str | None = None
    markdown_content: str | None = None


class KnowledgeBaseDocumentListView(CamelCaseModel):
    """当前知识库的真实文档列表。"""

    items: list[KnowledgeBaseDocumentView]


class UpdateKnowledgeBaseDocumentRequest(CamelCaseModel):
    """文档元数据或规范化 Markdown 的编辑请求。"""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    markdown_content: str | None = Field(default=None, min_length=1, max_length=20 * 1024 * 1024)


DEFAULT_ADVANCED_SEPARATORS = ["#"]


class KnowledgeBaseSettingsView(CamelCaseModel):
    knowledge_base_id: str
    mode: Literal["simple", "advanced"]
    max_characters: int
    overlap_characters: int
    separators: list[str]
    cleaning_rules: list[str]
    index_version: int
    updated_at: int


class UpdateKnowledgeBaseSettingsRequest(CamelCaseModel):
    mode: Literal["simple", "advanced"] = "simple"
    max_characters: int = Field(default=2400, ge=1, le=20000)
    overlap_characters: int = Field(default=240, ge=0, le=19999)
    separators: list[str] = Field(default_factory=lambda: list(DEFAULT_ADVANCED_SEPARATORS), min_length=1, max_length=20)
    cleaning_rules: list[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def validate_advanced_separator(self) -> "UpdateKnowledgeBaseSettingsRequest":
        if self.mode == "advanced" and len(self.separators) != 1:
            raise ValueError("高级分段只能选择一个分隔符")
        return self


class KnowledgeBaseSegmentPreviewRequest(UpdateKnowledgeBaseSettingsRequest):
    document_id: str = Field(min_length=1)


class KnowledgeBaseSegmentPreviewView(CamelCaseModel):
    document_id: str
    document_version: int
    mode: Literal["simple", "advanced"]
    segments: list["KnowledgeBaseSegmentView"]
    requires_rebuild: bool


class KnowledgeBaseSegmentView(CamelCaseModel):
    id: str
    document_id: str
    document_filename: str
    document_version: int
    ordinal: int
    content: str
    title_path: list[str]
    page_start: int | None
    page_end: int | None
    source_position: str | None
    index_status: Literal["pending", "ready", "failed"]
    chunk_strategy_version: str


class KnowledgeBaseSegmentListView(CamelCaseModel):
    items: list[KnowledgeBaseSegmentView]


class KnowledgeBaseSegmentRebuildView(CamelCaseModel):
    knowledge_base_id: str
    document_id: str
    chunk_count: int
    index_status: Literal["ready", "failed"]
    settings: KnowledgeBaseSettingsView


class KnowledgeBaseWorkspaceView(CamelCaseModel):
    id: str
    owner_teacher_id: str
    class_id: str
    source_knowledge_base_id: str | None
    kind: KnowledgeBaseKind
    name: str
    description: str
    status: KnowledgeBaseStatus
    source_version: int
    created_at: int
    updated_at: int
    documents: list[KnowledgeBaseDocumentView]


class KnowledgeBaseSearchRequest(CamelCaseModel):
    query: str = Field(min_length=1, max_length=500)
    limit: int = Field(default=8, ge=1, le=20)


class KnowledgeBaseRetrievalTestRequest(CamelCaseModel):
    query: str = Field(min_length=1, max_length=500)
    mode: Literal["keyword", "vector", "hybrid"] = "hybrid"
    top_k: int = Field(default=5, ge=1, le=20)
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)


class KnowledgeBaseSearchResultView(CamelCaseModel):
    chunk_id: str
    document_id: str
    document_filename: str
    document_version: int
    content: str
    title_path: list[str]
    page_start: int | None
    page_end: int | None
    source_position: str | None
    score: float


class KnowledgeBaseSearchView(CamelCaseModel):
    results: list[KnowledgeBaseSearchResultView]
    retrieval_mode: str
    has_results: bool
    query: str = ""
    top_k: int = 5
    min_score: float = 0.0
    fallback_reason: str | None = None


class KnowledgeBasePublicationView(CamelCaseModel):
    publication_id: str
    knowledge_base_id: str
    class_id: str
    version: int
    content_ids: list[str]
    created_at: int


class KnowledgeBaseIndexStatusView(CamelCaseModel):
    knowledge_base_id: str
    chunk_count: int
    ready_chunk_count: int
    retrieval_mode: str
    embedding_status: str
    chunk_strategy_version: str | None


class KnowledgeBaseBuildView(CamelCaseModel):
    knowledge_base_id: str
    processed_count: int
    succeeded_count: int
    failed_count: int
    pending_count: int
    embedding_status: str


class DocumentStatus(str, Enum):
    """文档版本的解析生命周期。"""

    UPLOADED = "uploaded"
    PARSING = "parsing"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"


@dataclass(frozen=True)
class KnowledgeBaseDocument:
    """知识库中的一个不可变文档版本。"""

    id: str
    knowledge_base_id: str
    original_filename: str
    file_format: str
    version: int
    status: DocumentStatus
    parser_name: str | None
    parser_version: str | None
    markdown: str | None
    content_sha256: str | None
    parse_error_code: str | None
    parse_error_message: str | None
    is_current: bool
    created_at: int
    updated_at: int


@dataclass(frozen=True)
class SearchResult:
    """带来源信息的关键词检索结果。"""

    chunk_id: str
    document_id: str
    knowledge_base_id: str
    document_filename: str
    document_version: int
    ordinal: int
    content: str
    title_path: tuple[str, ...]
    page_start: int | None
    page_end: int | None
    source_position: str | None
    rank: float
