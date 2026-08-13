from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.models import AuthPayload, LoginRequest, RegisterRequest, UserRole, UserView
from app.auth.service import AuthService
from app.common.api_response import ApiResponse
from app.common.errors import BusinessError
from app.common.responses import documented_error, success_response


router = APIRouter(prefix="/api/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)


def get_auth_service(request: Request) -> AuthService:
    return request.app.state.auth_service


def get_access_token(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise BusinessError(
            status_code=401,
            code="AUTH_SESSION_INVALID",
            message="登录状态已失效，请重新登录",
        )
    return credentials.credentials


def get_current_user(
    access_token: Annotated[str, Depends(get_access_token)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserView:
    return auth_service.authenticate(access_token)


def require_role(role: UserRole, *, message: str) -> Callable[[UserView], UserView]:
    """生成角色守卫依赖：角色不符时统一以 403 AUTH_ROLE_FORBIDDEN 拒绝。"""

    def guard(
        user: Annotated[UserView, Depends(get_current_user)],
    ) -> UserView:
        if user.role is not role:
            raise BusinessError(
                status_code=403,
                code="AUTH_ROLE_FORBIDDEN",
                message=message,
            )
        return user

    return guard


@router.post(
    "/register",
    response_model=ApiResponse[AuthPayload],
    status_code=status.HTTP_201_CREATED,
    responses={
        409: documented_error("用户名已存在"),
        422: documented_error("请求参数不正确"),
    },
)
def register(
    body: RegisterRequest,
    request: Request,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> ApiResponse[AuthPayload]:
    payload = auth_service.register(body)
    return success_response(
        request,
        code="AUTH_REGISTERED",
        message="注册成功",
        data=payload,
    )


@router.post(
    "/login",
    response_model=ApiResponse[AuthPayload],
    responses={
        401: documented_error("用户名或密码错误"),
        422: documented_error("请求参数不正确"),
    },
)
def login(
    body: LoginRequest,
    request: Request,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> ApiResponse[AuthPayload]:
    payload = auth_service.login(body)
    return success_response(
        request,
        code="AUTH_LOGGED_IN",
        message="登录成功",
        data=payload,
    )


@router.get(
    "/me",
    response_model=ApiResponse[UserView],
    responses={401: documented_error("登录状态已失效")},
)
def get_me(
    request: Request,
    user: Annotated[UserView, Depends(get_current_user)],
) -> ApiResponse[UserView]:
    return success_response(
        request,
        code="AUTH_SESSION_ACTIVE",
        message="登录状态有效",
        data=user,
    )


@router.post(
    "/logout",
    response_model=ApiResponse[None],
    responses={401: documented_error("登录状态已失效")},
)
def logout(
    request: Request,
    access_token: Annotated[str, Depends(get_access_token)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> ApiResponse[None]:
    auth_service.logout(access_token)
    return success_response(
        request,
        code="AUTH_LOGGED_OUT",
        message="已安全退出",
        data=None,
    )
