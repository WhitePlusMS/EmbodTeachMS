from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

from app.teaching_classes.mastery_models import MasteryLevel


class JoinPolicy(StrEnum):
    """教学班加入策略"""
    FREE = "free"
    APPROVAL = "approval"
    CLOSED = "closed"


class JoinRequestStatus(StrEnum):
    """加入申请状态"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class UploadStatus(StrEnum):
    """上传状态"""
    WAITING = "waiting"
    UPLOADED = "uploaded"


class ParseStatus(StrEnum):
    """解析状态"""
    NOT_STARTED = "not_started"
    PARSING = "parsing"
    COMPLETED = "completed"
    TIMED_OUT = "timed_out"
    FAILED = "failed"


class CurrentStep(StrEnum):
    """当前步骤"""
    UPLOAD = "upload"
    PARSING = "parsing"
    HIGHLIGHTING = "highlighting"
    QUESTIONING = "questioning"
    PUBLISHING = "publishing"


class FileFormat(StrEnum):
    """文件格式"""
    PDF = "pdf"
    DOCX = "docx"
    MARKDOWN = "markdown"


class CreateTeachingClassRequest(BaseModel):
    """创建教学班请求"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: str = Field(min_length=1, max_length=80)
    join_policy: JoinPolicy

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: object) -> object:
        """先清理名称空白，再由字段约束检查清理后的长度。"""
        if not isinstance(value, str):
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("班级名称不能为空或纯空白")
        return stripped


class UpdateJoinPolicyRequest(BaseModel):
    """更新加入策略请求"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    join_policy: JoinPolicy


class TeachingClassView(BaseModel):
    """教学班视图"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    id: str
    name: str
    join_policy: JoinPolicy
    member_count: int
    created_at: int
    updated_at: int


class TeachingClassListView(BaseModel):
    """教学班列表视图"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    items: list[TeachingClassView]


class DiscoverableClassView(BaseModel):
    """可发现教学班视图（学习者视角）"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    id: str
    name: str
    join_policy: JoinPolicy
    member_count: int
    created_at: int
    updated_at: int
    is_member: bool = False


class DiscoverableClassListView(BaseModel):
    """可发现教学班列表视图"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    items: list[DiscoverableClassView]


class LearnerClassListView(BaseModel):
    """学习者正式加入的教学班列表视图。"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    items: list[TeachingClassView]


class JoinClassResponse(BaseModel):
    """加入班级响应"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    class_id: str
    learner_id: str
    joined_at: int
    is_new_member: bool


class JoinRequestView(BaseModel):
    """加入申请视图"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    id: str
    class_id: str
    learner_id: str
    status: JoinRequestStatus
    created_at: int
    resolved_at: int | None
    resolved_by_teacher_id: str | None
    learner_display_name: str | None = None  # 教师视角：申请者显示名称
    class_name: str | None = None  # 学习者视角：班级名称


class JoinRequestListView(BaseModel):
    """加入申请列表视图"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    items: list[JoinRequestView]


class CreateJoinRequestResponse(BaseModel):
    """创建加入申请响应"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    request_id: str
    class_id: str
    learner_id: str
    status: JoinRequestStatus
    created_at: int
    is_new_request: bool


class ResolveJoinRequestRequest(BaseModel):
    """处理加入申请请求"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    status: JoinRequestStatus = Field(description="只能是approved或rejected")

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: JoinRequestStatus) -> JoinRequestStatus:
        if value not in [JoinRequestStatus.APPROVED, JoinRequestStatus.REJECTED]:
            raise ValueError("状态只能是approved或rejected")
        return value


class AuthorizationCodeView(BaseModel):
    """班级授权码视图"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    id: str
    class_id: str
    code: str
    enabled: bool
    expires_at: int | None
    created_at: int
    updated_at: int


class CreateOrUpdateAuthorizationCodeRequest(BaseModel):
    """创建或更新授权码请求"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    enabled: bool = Field(default=True)
    expires_at: int | None = Field(default=None, ge=1)


class JoinByAuthorizationCodeRequest(BaseModel):
    """通过授权码加入班级请求"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    code: str = Field(min_length=1)


class ResolveJoinRequestResponse(BaseModel):
    """处理加入申请响应"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    request_id: str
    class_id: str
    learner_id: str
    status: JoinRequestStatus
    resolved_at: int
    resolved_by_teacher_id: str
    membership_created: bool


class CourseOverview(BaseModel):
    """课程概述"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    knowledge_points: int
    knowledge_modules: int
    teaching_resources: int
    questions: int
    competency_objectives: int
    background: str
    introduction: str
    objectives: str
    features: str


class CourseOverviewCandidateView(BaseModel):
    """课程概述候选内容；候选必须由教师显式采用后才保存。"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    background: str = Field(min_length=1)
    introduction: str = Field(min_length=1)
    objectives: str = Field(min_length=1)
    features: str = Field(min_length=1)
    status: Literal["success", "degraded"]
    source: Literal["integrated", "demo", "unconfigured", "degraded"]
    message: str = Field(min_length=1)


class CourseOverviewCandidateText(BaseModel):
    """网关结构化候选文本，不向路由单独暴露。"""

    model_config = ConfigDict(extra="forbid")

    background: str = Field(min_length=1)
    introduction: str = Field(min_length=1)
    objectives: str = Field(min_length=1)
    features: str = Field(min_length=1)


class UpdateCourseOverviewRequest(BaseModel):
    """更新课程概述请求"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    background: str = Field(default="", min_length=0)
    introduction: str = Field(default="", min_length=0)
    objectives: str = Field(default="", min_length=0)
    features: str = Field(default="", min_length=0)


class PreparationSessionView(BaseModel):
    """备课会话视图"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    id: str
    class_id: str
    original_filename: str | None
    file_format: FileFormat | None
    file_size_bytes: int | None
    upload_status: UploadStatus
    parse_status: ParseStatus
    current_step: CurrentStep
    parsed_content_reference: str | None
    parse_error_code: str | None = None
    parse_started_at: int | None = None
    parse_completed_at: int | None = None
    highlights_json: str = "[]"
    candidate_questions_json: str
    publication_draft_json: str
    created_at: int
    updated_at: int
    knowledge_base_id: str | None = None
    selected_document_ids: list[str] = Field(default_factory=list)


class SelectPreparationDocumentsRequest(BaseModel):
    """从当前教学班知识库选择已完成索引的文档。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    document_ids: list[str] = Field(min_length=0, max_length=100)


class CreateOrUpdatePreparationSessionUploadRequest(BaseModel):
    """创建或更新备课会话上传请求"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    original_filename: str = Field(min_length=1)
    # 上传边界由服务层返回稳定业务错误码，不能让 Pydantic 先转换为泛用 422。
    file_format: str
    file_size_bytes: int = Field(gt=0)

    @field_validator("original_filename", mode="before")
    @classmethod
    def normalize_filename(cls, value: object) -> object:
        """清理文件名空白"""
        if not isinstance(value, str):
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("文件名不能为空或纯空白")
        return stripped


class PreparationSessionParagraphView(BaseModel):
    """创建教师可读取的知识库分段。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, serialize_by_alias=True)

    ordinal: int
    document_id: str | None = None
    document_filename: str | None = None
    block_type: str
    content: str


class PreparationSessionParsingResultView(BaseModel):
    """仅在解析成功后返回有序段落。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, serialize_by_alias=True)

    session: PreparationSessionView
    paragraphs: list[PreparationSessionParagraphView]


class HighlightView(BaseModel):
    """教学重点视图"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    id: str
    paragraph_ordinal: int
    start_offset: int
    end_offset: int
    created_at: int


class PreparationSessionParagraphWithHighlightsView(BaseModel):
    """带教学重点的知识库分段视图"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    ordinal: int
    document_id: str | None = None
    document_filename: str | None = None
    block_type: str
    content: str
    highlights: list[HighlightView]
    has_highlights: bool


class PreparationSessionParsingResultWithHighlightsView(BaseModel):
    """带教学重点的解析结果视图"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    session: PreparationSessionView
    paragraphs: list[PreparationSessionParagraphWithHighlightsView]
    total_highlights: int


class AddHighlightRequest(BaseModel):
    """新增教学重点请求"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    # Markdown 解析器按零基序号持久化段落，首段的合法序号是 0。
    paragraph_ordinal: int = Field(ge=0)
    start_offset: int = Field(ge=0)
    end_offset: int = Field(ge=0)

    @field_validator("end_offset")
    @classmethod
    def validate_offsets(cls, end_offset: int, info) -> int:
        """验证偏移量范围"""
        start_offset = info.data.get("start_offset", 0)
        if end_offset <= start_offset:
            raise ValueError("结束偏移必须大于开始偏移")
        return end_offset


class RemoveHighlightRequest(BaseModel):
    """取消教学重点请求"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    highlight_id: str = Field(min_length=1)


class QuestionType(StrEnum):
    """题目类型"""
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"


class QuestionSource(StrEnum):
    """题目来源"""
    MANUAL = "manual"
    CANDIDATE = "candidate"


class QuestionReviewStatus(StrEnum):
    """题目审核状态"""
    CANDIDATE = "candidate"
    CONFIRMED = "confirmed"


class QuestionView(BaseModel):
    """题目视图"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    id: str
    source: QuestionSource
    review_status: QuestionReviewStatus
    type: QuestionType
    stem: str
    options: list[str] = Field(min_length=1)
    answers: list[int] = Field(min_length=1)
    knowledge_points: list[str] = Field(min_length=1)
    highlight_source_ids: list[str]
    hint: str
    explanation: str
    created_at: int
    updated_at: int


class QuestionListView(BaseModel):
    """题目列表视图"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    items: list[QuestionView]
    is_publish_unlocked: bool = False
    can_generate_from_highlights: bool = False


class CandidateQuestionGenerationView(BaseModel):
    """小A候选题生成结果；候选仍需教师审核后才能发布。"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    items: list[QuestionView]
    status: Literal["success", "degraded"]
    source: Literal["integrated", "demo", "unconfigured", "degraded"]
    message: str = Field(min_length=1)


class QuestionWriteRequestBase(BaseModel):
    """创建/更新题目请求的共享字段与校验。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    type: QuestionType
    stem: str = Field(min_length=1)
    options: list[str] = Field(min_length=1)
    answers: list[int] = Field(min_length=1)
    knowledge_points: list[str] = Field(min_length=1)
    highlight_source_ids: list[str]
    hint: str = Field(default="")
    explanation: str = Field(default="")

    @field_validator("options")
    @classmethod
    def validate_options_unique(cls, options: list[str]) -> list[str]:
        """验证选项唯一性"""
        if len(options) != len(set(options)):
            raise ValueError("选项不能重复")
        return options

    @field_validator("answers")
    @classmethod
    def validate_answers(cls, answers: list[int], info) -> list[int]:
        """验证答案有效性"""
        options = info.data.get("options", [])
        if not options:
            return answers

        # 检查答案索引是否在选项范围内
        if any(answer < 0 or answer >= len(options) for answer in answers):
            raise ValueError("答案索引超出选项范围")

        # 检查题目类型与答案数量
        question_type = info.data.get("type")
        if question_type == QuestionType.SINGLE_CHOICE and len(answers) != 1:
            raise ValueError("单选题必须有且只有一个答案")

        if question_type == QuestionType.MULTIPLE_CHOICE and len(answers) < 1:
            raise ValueError("多选题至少需要一个答案")

        return sorted(answers)


class CreateQuestionRequest(QuestionWriteRequestBase):
    """创建题目请求"""


class GeneratedQuestionText(QuestionWriteRequestBase):
    """模型返回的单条候选题结构。"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )


class GeneratedCandidateQuestionsText(BaseModel):
    """模型返回的候选题集合，进入持久化前必须完整校验。"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )

    items: list[GeneratedQuestionText] = Field(min_length=1, max_length=10)


class UpdateQuestionRequest(QuestionWriteRequestBase):
    """更新题目请求"""


class ConfirmCandidateQuestionRequest(BaseModel):
    """确认候选题请求"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    question_id: str = Field(min_length=1)


class DeleteQuestionRequest(BaseModel):
    """删除题目请求"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    question_id: str = Field(min_length=1)


class ContentType(StrEnum):
    """内容类型"""
    KNOWLEDGE_POINT = "knowledge_point"
    KNOWLEDGE_MODULE = "knowledge_module"
    TEACHING_RESOURCE = "teaching_resource"
    QUESTION = "question"
    COMPETENCY_OBJECTIVE = "competency_objective"
    HOMEWORK = "homework"


class PublishedQuestionView(BaseModel):
    """学习者可见的结构化题目，不包含判分答案与解析。"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    type: QuestionType
    stem: str
    options: list[str] = Field(min_length=1)
    knowledge_points: list[str] = Field(default_factory=list)
    hint: str = ""


class PublishedContentView(BaseModel):
    """已发布内容视图"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    id: str
    class_id: str
    content_type: ContentType
    publication_status: str
    title: str
    content: str
    created_at: int
    updated_at: int
    # 作业特有字段
    due_at: int | None = None
    description: str | None = None
    question: PublishedQuestionView | None = None


class PublishedContentListView(BaseModel):
    """已发布内容列表视图"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    items: list[PublishedContentView]


class TeacherPublishedQuestionView(PublishedQuestionView):
    """仅教师已发布内容接口可见的完整题目事实。"""

    answers: list[int] = Field(min_length=1)
    explanation: str = ""


class TeacherPublishedContentView(PublishedContentView):
    """教师已发布内容视图。"""

    question: TeacherPublishedQuestionView | None = None


class TeacherPublishedContentListView(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    items: list[TeacherPublishedContentView]


class PublishedContentDetailView(BaseModel):
    """已发布内容详情视图，包含教学重点和来源信息"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    id: str
    class_id: str
    content_type: ContentType
    publication_status: str
    title: str
    content: str
    created_at: int
    updated_at: int
    # 作业特有字段
    due_at: int | None = None
    description: str | None = None
    # 教学重点信息
    highlights_json: str = "[]"
    # 来源信息
    source_preparation_session_id: str | None = None
    source_teacher_id: str | None = None
    source_filename: str | None = None
    question: PublishedQuestionView | None = None
    # 当前学习者是否已完成该内容
    completed: bool = False


class PublishHomeworkRequest(BaseModel):
    """发布作业请求"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    title: str = Field(max_length=200)
    due_at: int = Field(description="截止时间（Unix时间戳）")
    description: str = Field(default="", min_length=0, max_length=1000)

    @field_validator("due_at")
    @classmethod
    def validate_due_at(cls, due_at: int, info) -> int:
        """验证截止时间必须大于当前时间"""
        # 注意：实际验证需要在服务层使用now_provider获取当前时间
        # 这里只做基础格式验证
        if due_at <= 0:
            raise ValueError("截止时间必须为正数")
        return due_at

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: object) -> object:
        """清理标题空白"""
        if not isinstance(value, str):
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("标题不能为空或纯空白")
        return stripped


class PublishHomeworkResponse(BaseModel):
    """作业发布响应"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    session: PreparationSessionView
    homework_id: str


class CourseContentCompletionView(BaseModel):
    """课程内容完成记录视图"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    id: str
    learner_id: str
    class_id: str
    content_id: str
    completed_at: int
    created_at: int


class MarkContentCompleteRequest(BaseModel):
    """标记内容完成请求"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    class_id: str = Field(min_length=1)
    content_id: str = Field(min_length=1)


class CourseCompletionStatsView(BaseModel):
    """课程完成统计；所有完成率统一使用 0-1 比率。"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    total_contents: int = 0
    completed_contents: int = 0
    completion_rate: float = Field(default=0.0, ge=0, le=1, description="个人完成率（0-1）")


class KnowledgePointMasteryView(BaseModel):
    """知识点掌握详情"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    knowledge_point: str = Field(description="知识点")
    mastery_level: MasteryLevel = Field(description="掌握度级别")
    weighted_score: float = Field(description="加权总分")
    recent_evidence_count: int = Field(description="最近有效证据数量")
    first_correct_count: int = Field(description="首次正确题目数量")
    level_change: int = Field(description="级别变化：-1=下降，0=不变，1=上升")
    latest_evidence: dict[str, str | int] | None = Field(
        default=None,
        description="最近证据详情，包含questionId、resultType、createdAt"
    )


class MasterySummaryView(BaseModel):
    """掌握度摘要"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    status: str = "success"
    message: str = "掌握度分析完成"
    total_knowledge_points: int = Field(default=0, description="总知识点数量")
    level_distribution: dict[str, int] = Field(
        default_factory=lambda: {
            "unlearned": 0,
            "consolidating": 0,
            "basic_mastery": 0,
            "proficient_mastery": 0
        },
        description="各级别知识点数量分布"
    )
    knowledge_points: list[KnowledgePointMasteryView] = Field(
        default_factory=list,
        description="知识点掌握详情列表"
    )
    next_suggestion: str = Field(default="", description="下一步学习建议")


class CourseHomeSummaryView(BaseModel):
    """课程首页汇总视图"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    next_content: PublishedContentView | None = None
    content_list: list[PublishedContentView] = Field(default_factory=list)
    completion_stats: CourseCompletionStatsView = Field(default_factory=CourseCompletionStatsView)
    pending_homework: list[PublishedContentView] = Field(default_factory=list)
    next_suggestions: list[str] = Field(default_factory=list)
    mastery_summary: MasterySummaryView = Field(default_factory=MasterySummaryView)


class ClassroomPracticeAttemptView(BaseModel):
    """课堂练习作答记录视图"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    id: str
    learner_id: str
    class_id: str
    content_id: str
    selected_answers: list[int] = Field(min_length=0)  # 选中的答案索引列表
    is_correct: bool
    attempted_at: int
    created_at: int


class ClassroomPracticeAnswerBody(BaseModel):
    """课堂练习作答 HTTP 请求体；class_id/content_id 以路径参数为唯一来源"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    selected_answers: list[int] = Field(min_length=0)  # 允许空数组表示未选择

    @field_validator("selected_answers")
    @classmethod
    def validate_selected_answers(cls, selected_answers: list[int]) -> list[int]:
        """验证答案索引为非负整数"""
        if any(answer < 0 for answer in selected_answers):
            raise ValueError("答案索引不能为负数")
        return selected_answers


class ClassroomPracticeAnswerRequest(ClassroomPracticeAnswerBody):
    """课堂练习作答内部服务 DTO；class_id/content_id 由 router 从路径参数注入"""

    class_id: str = Field(min_length=1)
    content_id: str = Field(min_length=1)


class ClassroomPracticeResultView(BaseModel):
    """课堂练习核对结果视图"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    is_correct: bool
    correct_answers: list[int] = Field(min_length=0)  # 正确答案索引列表
    explanation: str = ""
    attempt: ClassroomPracticeAttemptView | None = None  # 保存的作答记录


class ClassroomPracticeContentDetailView(BaseModel):
    """课堂练习内容详情视图，包含题目信息和作答状态"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    content: PublishedContentDetailView
    attempt: ClassroomPracticeAttemptView | None = None
    can_submit: bool = True
    correct_answers: list[int] = Field(default_factory=list)
    explanation: str = ""

class HomeworkSubmissionStatus(StrEnum):
    """作业提交状态"""
    DRAFT = "draft"
    SUBMITTED = "submitted"


class HomeworkSubmissionView(BaseModel):
    """作业提交视图"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    id: str
    learner_id: str
    class_id: str
    homework_id: str
    status: HomeworkSubmissionStatus
    answers_json: str = "{}"  # JSON格式的答案映射
    grading_json: str = "{}"  # JSON格式的判分结果
    total_score: int = 0
    correct_count: int = 0
    draft_saved_at: int | None = None
    submitted_at: int | None = None
    is_late_submission: bool = False
    created_at: int
    updated_at: int


class HomeworkQuestionPreviewView(BaseModel):
    """作业题目预览视图（提交前），不包含答案信息"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    id: str
    type: QuestionType
    stem: str
    options: list[str] = Field(min_length=1)
    hint: str = ""


class HomeworkQuestionResultView(BaseModel):
    """作业题目结果视图（提交后），包含判分详情"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    id: str
    type: QuestionType
    stem: str
    options: list[str] = Field(min_length=1)
    hint: str = ""
    user_answers: list[int] = Field(min_length=0)
    correct_answers: list[int] = Field(min_length=0)
    is_correct: bool
    score: int = Field(ge=0)
    explanation: str = ""


class HomeworkSubmissionDetailView(BaseModel):
    """作业提交详情视图，包含作业内容和判分详情"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    submission: HomeworkSubmissionView | None = None
    homework: PublishedContentView  # 作业内容信息
    questions: list[HomeworkQuestionPreviewView | HomeworkQuestionResultView] = Field(default_factory=list)  # 作业题目列表


class SaveHomeworkDraftBody(BaseModel):
    """保存作业草稿 HTTP 请求体；class_id/homework_id 以路径参数为唯一来源"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    answers: dict[str, list[int]] = Field(default_factory=dict)  # 题目ID到答案索引的映射


class SaveHomeworkDraftRequest(SaveHomeworkDraftBody):
    """保存作业草稿内部服务 DTO；class_id/homework_id 由 router 从路径参数注入"""

    class_id: str = Field(min_length=1)
    homework_id: str = Field(min_length=1)


class SubmitHomeworkBody(BaseModel):
    """提交作业 HTTP 请求体；class_id/homework_id 以路径参数为唯一来源"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    answers: dict[str, list[int]] = Field(default_factory=dict)  # 题目ID到答案索引的映射

    @field_validator("answers")
    @classmethod
    def validate_answers(cls, answers: dict[str, list[int]]) -> dict[str, list[int]]:
        """验证答案格式"""
        for question_id, answer_indices in answers.items():
            if not isinstance(answer_indices, list):
                raise ValueError(f"题目 {question_id} 的答案必须是列表格式")
            if any(index < 0 for index in answer_indices):
                raise ValueError(f"题目 {question_id} 的答案索引不能为负数")
        return answers


class SubmitHomeworkRequest(SubmitHomeworkBody):
    """提交作业内部服务 DTO；class_id/homework_id 由 router 从路径参数注入"""

    class_id: str = Field(min_length=1)
    homework_id: str = Field(min_length=1)


class HomeworkSubmissionResultView(BaseModel):
    """作业提交结果视图"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    submission: HomeworkSubmissionView
    homework: PublishedContentView
    questions: list[HomeworkQuestionResultView] = Field(default_factory=list)  # 包含判分详情的题目列表


class HomeworkListView(BaseModel):
    """作业列表视图"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    items: list[PublishedContentView]
    submissions: dict[str, HomeworkSubmissionView] = Field(default_factory=dict)  # homework_id到提交记录的映射


class TeacherHomeworkQuestionStatsView(BaseModel):
    """教师作业逐题统计视图。"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    question_id: str = Field(description="题目ID")
    question_content: str = Field(description="题目内容")
    total_attempts: int = Field(default=0, description="已判分作答次数")
    correct_attempts: int = Field(default=0, description="判分正确次数")
    correct_rate: float | None = Field(default=None, description="正确率（0-100）；无数据时为空")
    common_error_reason: str | None = Field(default=None, description="结构化答案差异归纳的常见错因")


class TeacherHomeworkStatsView(BaseModel):
    """教师单份作业统计视图。"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    homework: PublishedContentView = Field(description="已发布作业")
    status: Literal["published"] = Field(default="published", description="作业发布状态")
    total_learners: int = Field(default=0, description="当前班正式成员数")
    submitted_count: int = Field(default=0, description="已提交人数")
    late_count: int = Field(default=0, description="迟交人数")
    correct_rate: float | None = Field(default=None, description="作业整体正确率（0-100）；无数据时为空")
    pending_review_count: int = Field(default=0, description="缺少确定性判分结果的提交数")
    data_status: Literal["ready", "no_submissions", "insufficient_data"] = Field(
        default="no_submissions", description="统计数据状态"
    )
    question_stats: list[TeacherHomeworkQuestionStatsView] = Field(
        default_factory=list, description="逐题统计"
    )
    ai_analysis: str | None = Field(
        default=None, description="AI 作业整体分析（含知识点掌握情况和常见问题）"
    )
    ai_suggestions: list[str] = Field(
        default_factory=list, description="AI 学习建议列表"
    )


class HomeworkAIAnalysisRequest(BaseModel):
    """AI 作业分析请求。"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )

    homework_id: str = Field(min_length=1)
    learner_id: str = Field(min_length=1)


class HomeworkAIAnalysisView(BaseModel):
    """AI 作业分析响应。"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    homework_id: str
    learner_id: str
    analysis: str | None = Field(description="AI 作业整体分析（含知识点掌握情况和常见问题）")
    suggestions: list[str] = Field(default_factory=list, description="AI 学习建议列表")
    source: str = Field(description="来源状态：integrated / demo / unconfigured / degraded")


class TeacherHomeworkListView(BaseModel):
    """教师作业管理列表视图。"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    items: list[TeacherHomeworkStatsView] = Field(default_factory=list)
    no_data: bool = Field(default=False, description="当前班没有已发布作业")


class MasteryDistributionView(BaseModel):
    """掌握度分布视图（匿名四级分布）"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    unlearned: int = Field(default=0, description="未学习人数")
    consolidating: int = Field(default=0, description="巩固中人数")
    basic_mastery: int = Field(default=0, description="基本掌握人数")
    proficient_mastery: int = Field(default=0, description="熟练掌握人数")


class ClassAggregateStatsView(BaseModel):
    """班级聚合统计视图"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    status: str = Field(default="success", description="响应状态")
    message: str = Field(default="", description="响应消息")

    # 基础统计
    total_members: int = Field(default=0, description="班级正式成员总数")
    content_completion_rate: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="课件平均完成率（0-1）",
    )
    at_least_one_completed: int = Field(default=0, description="至少完成一项内容的人数")

    # 掌握度分布（样本不足时为空）
    mastery_distribution: MasteryDistributionView | None = Field(default=None, description="掌握度分布")
    simulation_status: Literal["no_data"] = Field(
        default="no_data",
        description="Webots 尚无真实实训事实",
    )

    # 错误状态
    insufficient_sample: bool = Field(default=False, description="样本不足标记")
    no_data: bool = Field(default=False, description="无数据标记")


class TeacherDashboardLearnerPreviewView(BaseModel):
    """教师dashboard学习者预览视图"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    learner_id: str = Field(description="学习者ID")
    display_name: str = Field(description="学习者显示名称")
    completion_rate: float = Field(ge=0, le=1, description="个人完成率（0-1）")
    mastery_level: MasteryLevel = Field(description="主要掌握度级别")
    last_activity: int | None = Field(default=None, description="最后活动时间")


class TeacherDashboardHomeworkSummaryView(BaseModel):
    """作业摘要视图"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    total_homeworks: int = Field(default=0, description="总作业数")
    expected_submissions: int = Field(default=0, description="应提交总份数")
    pending_submissions: int = Field(default=0, description="待提交数")
    submitted_submissions: int = Field(default=0, description="已提交份数")
    late_submissions: int = Field(default=0, description="迟交份数")
    average_score: float | None = Field(default=None, description="已提交作业平均得分")


class TeacherDashboardConsolidationView(BaseModel):
    """待巩固知识点视图"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    knowledge_point: str = Field(description="知识点")
    learners_count: int = Field(description="需要巩固的学习者数")
    average_mastery: float = Field(description="平均掌握度分数")


class SimulationSummaryView(BaseModel):
    """只暴露 Webots 协议产生的结构化摘要，不暴露事件正文或本机路径。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, serialize_by_alias=True)

    source: Literal["demo"] = "demo"
    task_status: Literal["no_tasks", "configured"] = "no_tasks"
    connector_count: int = 0
    run_count: int = 0
    running_count: int = 0
    completed_count: int = 0
    failed_count: int = 0
    latest_terminal_status: Literal["completed", "failed"] | None = None
    latest_result: dict[str, object] | None = None


class TeacherDashboardView(BaseModel):
    """教师专用dashboard视图"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    # 基础统计
    total_members: int = Field(default=0, description="班级正式成员总数")
    content_completion_rate: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="课件平均完成率（0-1）",
    )
    at_least_one_completed: int = Field(default=0, description="至少完成一项内容的人数")

    # 掌握度分布（匿名四级分布）
    mastery_distribution: MasteryDistributionView = Field(
        default_factory=lambda: MasteryDistributionView(),
        description="掌握度分布"
    )

    # 高频提问状态
    questions_status: Literal["no_data"] = Field(
        default="no_data",
        description="当前没有结构化学习者提问事实",
    )

    # 待巩固知识点
    consolidation_topics: list[TeacherDashboardConsolidationView] = Field(
        default_factory=list,
        description="待巩固知识点列表"
    )

    # 作业摘要
    homework_summary: TeacherDashboardHomeworkSummaryView = Field(
        default_factory=lambda: TeacherDashboardHomeworkSummaryView(),
        description="作业摘要"
    )

    # Webots 实训状态
    simulation_status: Literal["no_data"] = Field(
        default="no_data",
        description="Webots 尚无真实实训事实"
    )

    # 学习者预览（固定上限5个）
    learner_previews: list[TeacherDashboardLearnerPreviewView] = Field(
        default_factory=list,
        description="学习者预览列表"
    )

    # 错误状态
    insufficient_sample: bool = Field(default=False, description="样本不足标记")
    no_data: bool = Field(default=False, description="无数据标记")


class LearnerListView(BaseModel):
    """学习者列表视图"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    items: list["LearnerPreviewView"] = Field(default_factory=list, description="学习者预览列表")


class LearnerPreviewView(BaseModel):
    """学习者预览视图"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    learner_id: str = Field(description="学习者ID")
    display_name: str = Field(description="学习者显示名称")
    completion_rate: float = Field(ge=0, le=1, description="个人完成率（0-1）")
    weakest_knowledge_point: str | None = Field(
        default=None,
        description="当前薄弱知识点；无结构化掌握证据时为空",
    )
    simulation_status: Literal["no_data"] = Field(
        default="no_data",
        description="Webots 尚无真实实训事实",
    )


class LearnerDetailView(BaseModel):
    """学习者详情视图"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    learner_id: str = Field(description="学习者ID")
    display_name: str = Field(description="学习者显示名称")
    completion_stats: CourseCompletionStatsView = Field(description="完成统计")
    mastery_summary: MasterySummaryView = Field(description="掌握度摘要")
    simulation_status: Literal["no_data"] = Field(
        default="no_data",
        description="Webots 尚无真实实训事实",
    )
