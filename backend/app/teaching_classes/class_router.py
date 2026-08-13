"""教学班 CRUD 路由：创建、列表、发现、加入、授权码。

注册到 /api/teaching-classes 前缀下。
"""
import logging

from fastapi import APIRouter, Response, status

from app.auth.models import UserView
from app.common.api_response import ApiResponse
from app.common.responses import documented_error, success_response
from app.teaching_classes._deps import (
    LearnerDep,
    Request,
    TeacherDep,
    TeachingClassServiceDep,
)
from app.teaching_classes.models import (
    AuthorizationCodeView,
    CreateJoinRequestResponse,
    CreateOrUpdateAuthorizationCodeRequest,
    CreateTeachingClassRequest,
    DiscoverableClassListView,
    JoinByAuthorizationCodeRequest,
    JoinClassResponse,
    JoinRequestListView,
    JoinRequestStatus,
    LearnerClassListView,
    ResolveJoinRequestRequest,
    ResolveJoinRequestResponse,
    TeachingClassListView,
    TeachingClassView,
    UpdateJoinPolicyRequest,
)

logger = logging.getLogger("course_agent.router.class")

router = APIRouter(prefix="/api/teaching-classes", tags=["teaching-classes"])


@router.post(
    "",
    response_model=ApiResponse[TeachingClassView],
    status_code=status.HTTP_201_CREATED,
    responses={403: documented_error("只有教师可以创建教学班"), 422: documented_error("请求参数不正确")},
)
def create_teaching_class(
    request: Request,
    body: CreateTeachingClassRequest,
    teacher: TeacherDep,
    service: TeachingClassServiceDep,
) -> ApiResponse[TeachingClassView]:
    """创建教学班"""
    teaching_class = service.create_class(body, teacher)
    return success_response(request, code="TEACHING_CLASS_CREATED", message="教学班创建成功", data=teaching_class)


@router.get(
    "",
    response_model=ApiResponse[TeachingClassListView],
    responses={403: documented_error("只有教师可以查看教学班列表")},
)
def list_teaching_classes(
    request: Request,
    teacher: TeacherDep,
    service: TeachingClassServiceDep,
) -> ApiResponse[TeachingClassListView]:
    """获取教师的教学班列表"""
    classes = service.list_teacher_classes(teacher)
    return success_response(request, code="TEACHING_CLASSES_LISTED", message="教学班列表获取成功", data=TeachingClassListView(items=classes))


@router.patch(
    "/{class_id}/join-policy",
    response_model=ApiResponse[TeachingClassView],
    responses={403: documented_error("只有教师可以修改教学班"), 404: documented_error("教学班不存在"), 422: documented_error("请求参数不正确")},
)
def update_join_policy(
    request: Request,
    class_id: str,
    body: UpdateJoinPolicyRequest,
    teacher: TeacherDep,
    service: TeachingClassServiceDep,
) -> ApiResponse[TeachingClassView]:
    """更新教学班加入策略"""
    teaching_class = service.update_join_policy(class_id, body, teacher)
    return success_response(request, code="TEACHING_CLASS_UPDATED", message="加入策略更新成功", data=teaching_class)


@router.get(
    "/discover",
    response_model=ApiResponse[DiscoverableClassListView],
    responses={403: documented_error("只有学习者可以访问发现功能")},
)
def discover_classes(
    request: Request,
    learner: LearnerDep,
    service: TeachingClassServiceDep,
) -> ApiResponse[DiscoverableClassListView]:
    """学习者发现可加入的教学班"""
    classes = service.discover_classes(learner)
    return success_response(request, code="CLASSES_DISCOVERED", message="教学班发现成功", data=DiscoverableClassListView(items=classes))


@router.get(
    "/mine",
    response_model=ApiResponse[LearnerClassListView],
    responses={403: documented_error("只有学习者可以查看我的课程")},
)
def list_learner_classes(
    request: Request,
    learner: LearnerDep,
    service: TeachingClassServiceDep,
) -> ApiResponse[LearnerClassListView]:
    """获取学习者已正式加入的教学班。"""
    return success_response(request, code="LEARNER_CLASSES_LISTED", message="我的课程加载成功", data=LearnerClassListView(items=service.list_learner_classes(learner)))


@router.get(
    "/{class_id}",
    response_model=ApiResponse[TeachingClassView],
    responses={403: documented_error("只有教师可以查看教学班详情"), 404: documented_error("教学班不存在")},
)
def get_teaching_class(
    request: Request,
    class_id: str,
    teacher: TeacherDep,
    service: TeachingClassServiceDep,
) -> ApiResponse[TeachingClassView]:
    """根据 ID 获取教学班详情。"""
    teaching_class = service.get_class_by_id(class_id, teacher)
    return success_response(request, code="TEACHING_CLASS_FETCHED", message="教学班详情获取成功", data=teaching_class)


@router.post(
    "/{class_id}/join",
    response_model=ApiResponse[JoinClassResponse],
    status_code=status.HTTP_201_CREATED,
    responses={403: documented_error("只有学习者可以加入教学班"), 404: documented_error("教学班不存在")},
)
def join_class(
    request: Request,
    class_id: str,
    learner: LearnerDep,
    service: TeachingClassServiceDep,
) -> ApiResponse[JoinClassResponse]:
    """学习者加入教学班"""
    result = service.join_class(class_id, learner)
    return success_response(request, code="CLASS_JOINED", message="加入教学班成功", data=result)


@router.post(
    "/{class_id}/join-request",
    response_model=ApiResponse[CreateJoinRequestResponse],
    status_code=status.HTTP_201_CREATED,
    responses={400: documented_error("申请已存在或已是成员"), 403: documented_error("只有学习者可以提交申请"), 404: documented_error("教学班不存在")},
)
def create_join_request(
    request: Request,
    class_id: str,
    learner: LearnerDep,
    service: TeachingClassServiceDep,
) -> ApiResponse[CreateJoinRequestResponse]:
    """学习者申请加入需要审批的教学班"""
    result = service.create_join_request(class_id, learner)
    return success_response(request, code="JOIN_REQUEST_CREATED", message="加入申请提交成功", data=result)


@router.get(
    "/{class_id}/join-requests",
    response_model=ApiResponse[JoinRequestListView],
    responses={403: documented_error("只有班级教师可以查看申请"), 404: documented_error("教学班不存在")},
)
def list_pending_join_requests(
    request: Request,
    class_id: str,
    teacher: TeacherDep,
    service: TeachingClassServiceDep,
) -> ApiResponse[JoinRequestListView]:
    """教师查看待处理的加入申请"""
    result = service.list_pending_join_requests(class_id, teacher)
    return success_response(request, code="JOIN_REQUESTS_LISTED", message="待处理申请获取成功", data=result)


@router.patch(
    "/join-requests/{request_id}/resolve",
    response_model=ApiResponse[ResolveJoinRequestResponse],
    responses={400: documented_error("申请已被处理"), 403: documented_error("只有班级教师可以处理申请"), 404: documented_error("申请不存在")},
)
def resolve_join_request(
    request: Request,
    request_id: str,
    body: ResolveJoinRequestRequest,
    teacher: TeacherDep,
    service: TeachingClassServiceDep,
) -> ApiResponse[ResolveJoinRequestResponse]:
    """教师审批或拒绝加入申请"""
    result = service.resolve_join_request(request_id, body, teacher)
    return success_response(
        request, code="JOIN_REQUEST_RESOLVED", message=f"申请{'批准' if body.status == JoinRequestStatus.APPROVED else '拒绝'}成功", data=result,
    )


@router.get(
    "/join-requests/mine",
    response_model=ApiResponse[JoinRequestListView],
    responses={403: documented_error("只有学习者可以查看自己的申请")},
)
def list_learner_join_requests(
    request: Request,
    learner: LearnerDep,
    service: TeachingClassServiceDep,
) -> ApiResponse[JoinRequestListView]:
    """学习者查看自己的加入申请"""
    result = service.get_learner_join_requests(learner)
    return success_response(request, code="LEARNER_JOIN_REQUESTS_LISTED", message="我的申请列表获取成功", data=result)


@router.get(
    "/{class_id}/authorization-code",
    response_model=ApiResponse[AuthorizationCodeView | None],
    responses={403: documented_error("只有班级教师可以查看授权码"), 404: documented_error("教学班不存在")},
)
def get_authorization_code(
    request: Request,
    class_id: str,
    teacher: TeacherDep,
    service: TeachingClassServiceDep,
) -> ApiResponse[AuthorizationCodeView | None]:
    """获取教学班的授权码"""
    auth_code = service.get_authorization_code(class_id, teacher)
    return success_response(request, code="AUTHORIZATION_CODE_FETCHED", message="授权码获取成功", data=auth_code)


@router.put(
    "/{class_id}/authorization-code",
    response_model=ApiResponse[AuthorizationCodeView],
    responses={400: documented_error("过期时间无效"), 403: documented_error("只有班级教师可以管理授权码"), 404: documented_error("教学班不存在"), 422: documented_error("请求参数不正确")},
)
def create_or_update_authorization_code(
    request: Request,
    class_id: str,
    body: CreateOrUpdateAuthorizationCodeRequest,
    teacher: TeacherDep,
    service: TeachingClassServiceDep,
) -> ApiResponse[AuthorizationCodeView]:
    """创建或更新教学班授权码"""
    auth_code = service.create_or_update_authorization_code(class_id, body, teacher)
    return success_response(request, code="AUTHORIZATION_CODE_UPDATED", message="授权码更新成功", data=auth_code)


@router.post(
    "/join-by-authorization-code",
    response_model=ApiResponse[JoinClassResponse],
    status_code=status.HTTP_201_CREATED,
    responses={400: documented_error("授权码无效"), 403: documented_error("只有学习者可以使用授权码加入"), 404: documented_error("教学班不存在"), 422: documented_error("请求参数不正确")},
)
def join_class_by_authorization_code(
    request: Request,
    body: JoinByAuthorizationCodeRequest,
    learner: LearnerDep,
    service: TeachingClassServiceDep,
) -> ApiResponse[JoinClassResponse]:
    """通过授权码加入教学班"""
    result = service.join_class_by_authorization_code(body, learner)
    return success_response(request, code="CLASS_JOINED_BY_AUTHORIZATION_CODE", message="通过授权码加入教学班成功", data=result)
