"""LLM 网关的严格业务 DTO。"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatGatewayRequest(BaseModel):
    """对话网关输入，不绑定厂商消息协议。"""

    model_config = ConfigDict(extra="forbid")

    system_text: str = Field(min_length=1, max_length=4000)
    input_text: str = Field(min_length=1, max_length=12000)
    response_format: Literal["text", "json"] = "text"


class ChatGatewayResult(BaseModel):
    """对话网关输出和来源状态。"""

    model_config = ConfigDict(extra="forbid")

    text: str = ""
    status: Literal["success", "degraded"]
    source: Literal["integrated", "demo", "unconfigured", "degraded"]
    attempts: int = Field(default=0, ge=0)
    failure_code: str | None = None
