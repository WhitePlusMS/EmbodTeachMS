from fastapi import Request

from app.common.api_response import ApiResponse


def documented_error(message: str) -> dict[str, object]:
    """为 OpenAPI 声明统一错误 DTO，避免生成框架默认错误类型。"""
    return {"model": ApiResponse[None], "description": message}


def success_response[Payload](
    request: Request,
    *,
    code: str,
    message: str,
    data: Payload,
) -> ApiResponse[Payload]:
    """构造带请求标识的统一成功响应。"""
    return ApiResponse(
        code=code,
        message=message,
        data=data,
        request_id=request.state.request_id,
    )
