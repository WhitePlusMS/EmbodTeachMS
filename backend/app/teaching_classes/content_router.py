"""课程内容路由：课程概述、已发布内容、首页摘要、知识库。

prefix=/api/teaching-classes
"""
from fastapi import APIRouter

from app.auth.models import UserView
from app.common.api_response import ApiResponse
from app.common.responses import documented_error, success_response
from app.knowledge_bases.models import KnowledgeBaseSearchRequest, KnowledgeBaseSearchView, KnowledgeBaseWorkspaceView
from app.teaching_classes._deps import (
    ContentQueryDep,
    CourseOverviewDep,
    CurrentUserDep,
    KnowledgeBaseServiceDep,
    LearnerDep,
    Request,
    TeacherDep,
)
from app.teaching_classes.models import (
    CourseContentCompletionView,
    CourseHomeSummaryView,
    CourseOverview,
    CourseOverviewCandidateView,
    MarkContentCompleteRequest,
    PublishedContentDetailView,
    PublishedContentListView,
    TeacherPublishedContentListView,
    UpdateCourseOverviewRequest,
)

router = APIRouter(prefix="/api/teaching-classes", tags=["teaching-classes"])


# ── 知识库 ──────────────────────────────────────────────────────────

@router.get(
    "/{class_id}/knowledge-base",
    response_model=ApiResponse[KnowledgeBaseWorkspaceView | None],
    responses={403: documented_error("只有班级教师可以查看知识库"), 404: documented_error("教学班不存在")},
)
def get_class_knowledge_base(
    request: Request,
    class_id: str,
    teacher: TeacherDep,
    service: KnowledgeBaseServiceDep,
) -> ApiResponse[KnowledgeBaseWorkspaceView | None]:
    workspace = service.get_for_class(class_id, teacher)
    return success_response(
        request, code="CLASS_KNOWLEDGE_BASE_FETCHED",
        message="教学班知识库获取成功" if workspace else "教学班暂无知识库副本", data=workspace,
    )


@router.post(
    "/{class_id}/knowledge-base/search",
    response_model=ApiResponse[KnowledgeBaseSearchView],
    responses={404: documented_error("教学班不存在或无权访问")},
)
def search_class_knowledge_base(
    request: Request,
    class_id: str,
    body: KnowledgeBaseSearchRequest,
    user: CurrentUserDep,
    service: KnowledgeBaseServiceDep,
) -> ApiResponse[KnowledgeBaseSearchView]:
    result = service.search_for_class_member(class_id, body.query, body.limit, user)
    return success_response(request, code="CLASS_KNOWLEDGE_BASE_SEARCHED", message="教学班知识库检索完成", data=result)


# ── 课程概述 ───────────────────────────────────────────────────────

@router.get(
    "/{class_id}/course-overview",
    response_model=ApiResponse[CourseOverview],
    responses={403: documented_error("只有班级教师可以查看课程概述"), 404: documented_error("教学班不存在")},
)
def get_course_overview(
    request: Request,
    class_id: str,
    teacher: TeacherDep,
    overview: CourseOverviewDep,
) -> ApiResponse[CourseOverview]:
    overview_data = overview.get_course_overview(class_id, teacher)
    return success_response(request, code="COURSE_OVERVIEW_FETCHED", message="课程概述获取成功", data=overview_data)


@router.put(
    "/{class_id}/course-overview",
    response_model=ApiResponse[CourseOverview],
    responses={403: documented_error("只有班级教师可以更新课程概述"), 404: documented_error("教学班不存在"), 422: documented_error("请求参数不正确")},
)
def update_course_overview(
    request: Request,
    class_id: str,
    body: UpdateCourseOverviewRequest,
    teacher: TeacherDep,
    overview: CourseOverviewDep,
) -> ApiResponse[CourseOverview]:
    overview_data = overview.update_course_overview(class_id, body, teacher)
    return success_response(request, code="COURSE_OVERVIEW_UPDATED", message="课程概述更新成功", data=overview_data)


@router.post(
    "/{class_id}/course-overview/candidates",
    response_model=ApiResponse[CourseOverviewCandidateView],
    responses={403: documented_error("只有班级教师可以生成课程概述候选"), 404: documented_error("教学班不存在")},
)
def generate_course_overview_candidates(
    request: Request,
    class_id: str,
    teacher: TeacherDep,
    overview: CourseOverviewDep,
) -> ApiResponse[CourseOverviewCandidateView]:
    candidate = overview.generate_course_overview_candidates(class_id, teacher)
    return success_response(request, code="COURSE_OVERVIEW_CANDIDATES_GENERATED", message=candidate.message, data=candidate)


# ── 已发布内容 ─────────────────────────────────────────────────────

@router.get(
    "/{class_id}/published-contents",
    response_model=ApiResponse[TeacherPublishedContentListView],
    responses={403: documented_error("只有班级教师可以查看已发布内容"), 404: documented_error("教学班不存在")},
)
def list_published_contents(
    request: Request,
    class_id: str,
    teacher: TeacherDep,
    content_query: ContentQueryDep,
) -> ApiResponse[TeacherPublishedContentListView]:
    contents = content_query.list_published_contents(class_id, teacher)
    return success_response(request, code="PUBLISHED_CONTENTS_LISTED", message="已发布内容获取成功", data=contents)


@router.get(
    "/{class_id}/published-contents/learner",
    response_model=ApiResponse[PublishedContentListView],
    responses={403: documented_error("只有班级正式成员可以查看已发布内容"), 404: documented_error("教学班不存在")},
)
def list_published_contents_for_learner(
    request: Request,
    class_id: str,
    learner: LearnerDep,
    content_query: ContentQueryDep,
) -> ApiResponse[PublishedContentListView]:
    contents = content_query.list_published_contents_for_learner(class_id, learner)
    return success_response(request, code="PUBLISHED_CONTENTS_LISTED", message="已发布内容获取成功", data=contents)


@router.get(
    "/{class_id}/published-contents/{content_id}/learner",
    response_model=ApiResponse[PublishedContentDetailView],
    responses={403: documented_error("只有班级正式成员可以查看课程内容"), 404: documented_error("课程内容不存在")},
)
def get_published_content_detail_for_learner(
    request: Request,
    class_id: str,
    content_id: str,
    learner: LearnerDep,
    content_query: ContentQueryDep,
) -> ApiResponse[PublishedContentDetailView]:
    content_detail = content_query.get_published_content_detail_for_learner(class_id, content_id, learner)
    return success_response(request, code="PUBLISHED_CONTENT_DETAIL_FETCHED", message="课程内容详情获取成功", data=content_detail)


# ── 内容完成 ───────────────────────────────────────────────────────

@router.post(
    "/{class_id}/contents/{content_id}/complete",
    response_model=ApiResponse[CourseContentCompletionView],
    status_code=201,
    responses={403: documented_error("只有班级正式成员可以标记内容完成"), 404: documented_error("课程内容不存在或未发布")},
)
def mark_content_complete(
    request: Request,
    class_id: str,
    content_id: str,
    learner: LearnerDep,
    content_query: ContentQueryDep,
) -> ApiResponse[CourseContentCompletionView]:
    completion = content_query.mark_content_complete(MarkContentCompleteRequest(class_id=class_id, content_id=content_id), learner)
    return success_response(request, code="CONTENT_MARKED_COMPLETE", message="课程内容标记完成成功", data=completion)


# ── 课程首页汇总 ──────────────────────────────────────────────────

@router.get(
    "/{class_id}/home-summary",
    response_model=ApiResponse[CourseHomeSummaryView],
    responses={403: documented_error("只有班级正式成员可以查看课程首页汇总"), 404: documented_error("教学班不存在")},
)
def get_course_home_summary(
    request: Request,
    class_id: str,
    learner: LearnerDep,
    content_query: ContentQueryDep,
) -> ApiResponse[CourseHomeSummaryView]:
    summary = content_query.get_course_home_summary(class_id, learner)
    return success_response(request, code="COURSE_HOME_SUMMARY_FETCHED", message="课程首页汇总获取成功", data=summary)
