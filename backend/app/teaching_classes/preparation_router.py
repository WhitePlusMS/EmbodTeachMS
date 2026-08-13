"""备课路由：备课会话 CRUD、文件上传、解析、教学重点、题目、发布。

prefix=/api/teaching-classes
"""
from fastapi import APIRouter, File, Response, UploadFile, status

from app.common.api_response import ApiResponse
from app.common.responses import documented_error, success_response
from app.teaching_classes._deps import (
    PreparationSessionDep,
    PublicationModuleDep,
    Request,
    TeacherDep,
)
from app.teaching_classes.models import (
    AddHighlightRequest,
    CandidateQuestionGenerationView,
    ConfirmCandidateQuestionRequest,
    CreateQuestionRequest,
    DeleteQuestionRequest,
    HighlightView,
    PreparationSessionParsingResultView,
    PreparationSessionParsingResultWithHighlightsView,
    PreparationSessionView,
    PublishHomeworkRequest,
    PublishHomeworkResponse,
    QuestionListView,
    QuestionView,
    RemoveHighlightRequest,
    SelectPreparationDocumentsRequest,
    UpdateQuestionRequest,
)

router = APIRouter(prefix="/api/teaching-classes", tags=["teaching-classes"])


@router.post(
    "/{class_id}/preparation-session",
    response_model=ApiResponse[PreparationSessionView],
    responses={201: {"model": ApiResponse[PreparationSessionView], "description": "备课会话创建成功"},
               403: documented_error("只有教师可以创建备课会话"), 404: documented_error("教学班不存在")},
)
def create_or_get_preparation_session(
    request: Request,
    response: Response,
    class_id: str,
    teacher: TeacherDep,
    preparation_sessions: PreparationSessionDep,
) -> ApiResponse[PreparationSessionView]:
    session, is_new = preparation_sessions.get_or_create_preparation_session(class_id, teacher)
    response.status_code = status.HTTP_201_CREATED if is_new else status.HTTP_200_OK
    return success_response(
        request, code="PREPARATION_SESSION_CREATED" if is_new else "PREPARATION_SESSION_FETCHED",
        message="备课会话创建成功" if is_new else "备课会话获取成功", data=session,
    )


@router.get(
    "/{class_id}/preparation-session",
    response_model=ApiResponse[PreparationSessionView],
    responses={403: documented_error("只有教师可以查看备课会话"), 404: documented_error("备课会话不存在")},
)
def get_preparation_session(
    request: Request,
    class_id: str,
    teacher: TeacherDep,
    preparation_sessions: PreparationSessionDep,
) -> ApiResponse[PreparationSessionView]:
    session = preparation_sessions.get_preparation_session(class_id, teacher)
    return success_response(request, code="PREPARATION_SESSION_FETCHED", message="备课会话获取成功", data=session)


@router.put(
    "/{class_id}/preparation-session/upload",
    response_model=ApiResponse[PreparationSessionView],
    responses={403: documented_error("只有教师可以上传文件"), 404: documented_error("备课会话不存在"), 422: documented_error("不支持的上传格式或文件过大")},
)
def update_preparation_session_upload(
    request: Request,
    class_id: str,
    teacher: TeacherDep,
    preparation_sessions: PreparationSessionDep,
    file: UploadFile = File(...),
) -> ApiResponse[PreparationSessionView]:
    session = preparation_sessions.replace_preparation_session_file(class_id, file.filename or "", file.file.read(), teacher)
    return success_response(request, code="PREPARATION_SESSION_FILE_REPLACED", message="备课会话文件替换成功", data=session)


@router.post("/{class_id}/preparation-session/parse", response_model=ApiResponse[PreparationSessionView])
def start_preparation_session_parsing(
    request: Request,
    class_id: str,
    teacher: TeacherDep,
    preparation_sessions: PreparationSessionDep,
) -> ApiResponse[PreparationSessionView]:
    session = preparation_sessions.start_preparation_session_parsing(class_id, teacher)
    return success_response(request, code="PREPARATION_SESSION_PARSING_STARTED", message="文档解析已开始", data=session)


@router.get("/{class_id}/preparation-session/parsed-paragraphs", response_model=ApiResponse[PreparationSessionParsingResultView])
def get_preparation_session_parsed_paragraphs(
    request: Request,
    class_id: str,
    teacher: TeacherDep,
    preparation_sessions: PreparationSessionDep,
) -> ApiResponse[PreparationSessionParsingResultView]:
    session = preparation_sessions.get_preparation_session(class_id, teacher)
    paragraphs = preparation_sessions.get_preparation_session_paragraphs(class_id, teacher)
    return success_response(request, code="PREPARATION_SESSION_PARSED_PARAGRAPHS_FETCHED", message="解析结果获取成功", data=PreparationSessionParsingResultView(session=session, paragraphs=paragraphs))


@router.get(
    "/{class_id}/preparation-session/parsed-paragraphs-with-highlights",
    response_model=ApiResponse[PreparationSessionParsingResultWithHighlightsView],
    responses={403: documented_error("只有教师可以查看备课会话"), 404: documented_error("备课会话不存在")},
)
def get_preparation_session_parsed_paragraphs_with_highlights(
    request: Request,
    class_id: str,
    teacher: TeacherDep,
    preparation_sessions: PreparationSessionDep,
) -> ApiResponse[PreparationSessionParsingResultWithHighlightsView]:
    result = preparation_sessions.get_preparation_session_paragraphs_with_highlights(class_id, teacher)
    return success_response(request, code="PREPARATION_SESSION_PARSED_PARAGRAPHS_WITH_HIGHLIGHTS_FETCHED", message="带教学重点的解析结果获取成功", data=result)


@router.post(
    "/{class_id}/preparation-session/highlights",
    response_model=ApiResponse[HighlightView],
    status_code=status.HTTP_201_CREATED,
    responses={400: documented_error("教学重点添加失败"), 403: documented_error("只有教师可以添加教学重点"), 404: documented_error("备课会话或段落不存在"), 409: documented_error("教学重点冲突")},
)
def add_highlight(
    request: Request,
    class_id: str,
    body: AddHighlightRequest,
    teacher: TeacherDep,
    preparation_sessions: PreparationSessionDep,
) -> ApiResponse[HighlightView]:
    highlight = preparation_sessions.add_highlight(class_id, body, teacher)
    return success_response(request, code="HIGHLIGHT_ADDED", message="教学重点添加成功", data=highlight)


@router.delete(
    "/{class_id}/preparation-session/highlights",
    response_model=ApiResponse[None],
    responses={400: documented_error("教学重点取消失败"), 403: documented_error("只有教师可以取消教学重点"), 404: documented_error("教学重点不存在")},
)
def remove_highlight(
    request: Request,
    class_id: str,
    body: RemoveHighlightRequest,
    teacher: TeacherDep,
    preparation_sessions: PreparationSessionDep,
) -> ApiResponse[None]:
    preparation_sessions.remove_highlight(class_id, body, teacher)
    return success_response(request, code="HIGHLIGHT_REMOVED", message="教学重点取消成功", data=None)


@router.get(
    "/{class_id}/preparation-session/questions",
    response_model=ApiResponse[QuestionListView],
    responses={403: documented_error("只有教师可以查看题目"), 404: documented_error("备课会话不存在")},
)
def list_questions(
    request: Request,
    class_id: str,
    teacher: TeacherDep,
    preparation_sessions: PreparationSessionDep,
) -> ApiResponse[QuestionListView]:
    questions = preparation_sessions.list_questions(class_id, teacher)
    return success_response(request, code="QUESTIONS_LISTED", message="题目列表获取成功", data=questions)


@router.post(
    "/{class_id}/preparation-session/questions",
    response_model=ApiResponse[QuestionView],
    status_code=status.HTTP_201_CREATED,
    responses={400: documented_error("题目创建失败"), 403: documented_error("只有教师可以创建题目"), 404: documented_error("备课会话不存在")},
)
def create_question(
    request: Request,
    class_id: str,
    body: CreateQuestionRequest,
    teacher: TeacherDep,
    preparation_sessions: PreparationSessionDep,
) -> ApiResponse[QuestionView]:
    question = preparation_sessions.create_question(class_id, body, teacher)
    return success_response(request, code="QUESTION_CREATED", message="题目创建成功", data=question)


@router.put(
    "/{class_id}/preparation-session/questions/{question_id}",
    response_model=ApiResponse[QuestionView],
    responses={400: documented_error("题目更新失败"), 403: documented_error("只有教师可以更新题目"), 404: documented_error("题目不存在")},
)
def update_question(
    request: Request,
    class_id: str,
    question_id: str,
    body: UpdateQuestionRequest,
    teacher: TeacherDep,
    preparation_sessions: PreparationSessionDep,
) -> ApiResponse[QuestionView]:
    question = preparation_sessions.update_question(class_id, question_id, body, teacher)
    return success_response(request, code="QUESTION_UPDATED", message="题目更新成功", data=question)


@router.post(
    "/{class_id}/preparation-session/questions/confirm",
    response_model=ApiResponse[QuestionView],
    responses={400: documented_error("候选题确认失败"), 403: documented_error("只有教师可以确认候选题"), 404: documented_error("题目不存在")},
)
def confirm_candidate_question(
    request: Request,
    class_id: str,
    body: ConfirmCandidateQuestionRequest,
    teacher: TeacherDep,
    preparation_sessions: PreparationSessionDep,
) -> ApiResponse[QuestionView]:
    question = preparation_sessions.confirm_candidate_question(class_id, body, teacher)
    return success_response(request, code="QUESTION_CONFIRMED", message="候选题确认成功", data=question)


@router.post(
    "/{class_id}/preparation-session/questions/candidates",
    response_model=ApiResponse[CandidateQuestionGenerationView],
    responses={400: documented_error("没有可用教学重点"), 403: documented_error("只有教师可以生成候选题"), 404: documented_error("备课会话不存在")},
)
def generate_candidate_questions(
    request: Request,
    class_id: str,
    teacher: TeacherDep,
    preparation_sessions: PreparationSessionDep,
) -> ApiResponse[CandidateQuestionGenerationView]:
    result = preparation_sessions.generate_candidate_questions(class_id, teacher)
    return success_response(request, code="CANDIDATE_QUESTIONS_GENERATED", message=result.message, data=result)


@router.delete(
    "/{class_id}/preparation-session/questions",
    response_model=ApiResponse[None],
    responses={400: documented_error("题目删除失败"), 403: documented_error("只有教师可以删除题目"), 404: documented_error("题目不存在")},
)
def delete_question(
    request: Request,
    class_id: str,
    body: DeleteQuestionRequest,
    teacher: TeacherDep,
    preparation_sessions: PreparationSessionDep,
) -> ApiResponse[None]:
    preparation_sessions.delete_question(class_id, body, teacher)
    return success_response(request, code="QUESTION_DELETED", message="题目删除成功", data=None)


@router.post(
    "/{class_id}/preparation-session/publish",
    response_model=ApiResponse[PreparationSessionView],
    responses={400: documented_error("发布条件不满足"), 403: documented_error("只有教师可以发布备课会话"), 404: documented_error("备课会话不存在"), 409: documented_error("备课会话已发布，不能重复发布")},
)
def publish_preparation_session(
    request: Request,
    class_id: str,
    teacher: TeacherDep,
    publication_module: PublicationModuleDep,
) -> ApiResponse[PreparationSessionView]:
    session = publication_module.publish(class_id, teacher)
    return success_response(request, code="PREPARATION_SESSION_PUBLISHED", message="备课会话发布成功", data=session)


@router.post(
    "/{class_id}/preparation-session/publish-homework",
    response_model=ApiResponse[PublishHomeworkResponse],
    responses={400: documented_error("发布条件不满足或字段非法"), 403: documented_error("只有教师可以发布作业"), 404: documented_error("备课会话不存在"), 409: documented_error("备课会话已发布，不能重复发布")},
)
def publish_homework(
    request: Request,
    class_id: str,
    body: PublishHomeworkRequest,
    teacher: TeacherDep,
    publication_module: PublicationModuleDep,
) -> ApiResponse[PublishHomeworkResponse]:
    result = publication_module.publish_homework(class_id, body, teacher)
    return success_response(request, code="HOMEWORK_PUBLISHED", message="作业发布成功", data=result)


@router.post(
    "/{class_id}/preparation-session/documents",
    response_model=ApiResponse[PreparationSessionView],
    responses={403: documented_error("只有教师可以选择备课文档"), 404: documented_error("备课文档或会话不存在"), 409: documented_error("备课文档尚未准备好")},
)
def select_preparation_session_documents(
    request: Request,
    class_id: str,
    body: SelectPreparationDocumentsRequest,
    teacher: TeacherDep,
    preparation_sessions: PreparationSessionDep,
) -> ApiResponse[PreparationSessionView]:
    session = preparation_sessions.select_knowledge_base_documents(class_id, body, teacher)
    return success_response(request, code="PREPARATION_SESSION_DOCUMENTS_SELECTED", message="备课文档选择成功", data=session)
