from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.auth.models import UserRole, UserView
from app.auth.router import require_role
from app.common.api_response import ApiResponse
from app.common.responses import documented_error, success_response
from app.workspaces.models import WorkspaceView


router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])

require_learner = require_role(UserRole.LEARNER, message="当前角色无权访问该工作台")
require_teacher = require_role(UserRole.TEACHER, message="当前角色无权访问该工作台")


@router.get(
    "/learner",
    response_model=ApiResponse[WorkspaceView],
    responses={
        401: documented_error("登录状态已失效"),
        403: documented_error("角色无权访问"),
    },
)
def get_learner_workspace(
    request: Request,
    _user: Annotated[UserView, Depends(require_learner)],
) -> ApiResponse[WorkspaceView]:
    return success_response(
        request,
        code="WORKSPACE_READY",
        message="学习者工作台加载成功",
        data=WorkspaceView(
            role=UserRole.LEARNER,
            title="我的课程",
            navigation=["我的课程"],
        ),
    )


@router.get(
    "/teacher",
    response_model=ApiResponse[WorkspaceView],
    responses={
        401: documented_error("登录状态已失效"),
        403: documented_error("角色无权访问"),
    },
)
def get_teacher_workspace(
    request: Request,
    _user: Annotated[UserView, Depends(require_teacher)],
) -> ApiResponse[WorkspaceView]:
    return success_response(
        request,
        code="WORKSPACE_READY",
        message="教师工作台加载成功",
        data=WorkspaceView(
            role=UserRole.TEACHER,
            title="我的课程",
            navigation=["我的课程"],
        ),
    )
