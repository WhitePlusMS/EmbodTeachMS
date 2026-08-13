"""可注入 transport 的可替换 LLM 网关实现。"""

import json
import logging
import os
import re
import time
from collections.abc import Callable
from typing import Protocol
from urllib import error as url_error
from urllib import request as url_request

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.llm_gateway.models import ChatGatewayRequest, ChatGatewayResult

logger = logging.getLogger("course_agent.llm_gateway")


class ChatGateway(Protocol):
    """对话网关窄接口。"""

    def generate(self, request: ChatGatewayRequest) -> ChatGatewayResult:
        ...


ChatTransport = Callable[[ChatGatewayRequest, float], object]


class OpenAICompatibleChatTransport:
    """调用 OpenAI 兼容聊天接口并归一化为网关文本。"""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        opener: Callable[..., object] = url_request.urlopen,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._opener = opener

    def __call__(self, request: ChatGatewayRequest, timeout: float) -> dict[str, str]:
        provider_payload: dict[str, object] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": request.system_text},
                {"role": "user", "content": request.input_text},
            ],
            "stream": False,
            "thinking": {"type": "disabled"},
            "temperature": 0.2,
        }
        if request.response_format == "json":
            provider_payload["response_format"] = {"type": "json_object"}
        payload = json.dumps(provider_payload, ensure_ascii=False).encode("utf-8")
        http_request = url_request.Request(
            f"{self._base_url}/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with self._opener(http_request, timeout=timeout) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except TimeoutError:
            raise
        except url_error.HTTPError as error:
            raise OSError(f"PROVIDER_HTTP_{error.code}") from error
        except (url_error.URLError, OSError) as error:
            raise OSError("PROVIDER_REQUEST_FAILED") from error
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("PROVIDER_RESPONSE_INVALID") from error

        if not isinstance(response_payload, dict):
            raise ValueError("PROVIDER_RESPONSE_INVALID")
        choices = response_payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("PROVIDER_RESPONSE_INVALID")
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise ValueError("PROVIDER_RESPONSE_INVALID")
        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise ValueError("PROVIDER_RESPONSE_INVALID")
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("PROVIDER_RESPONSE_INVALID")
        return {"text": content}


class ProviderChatResponse(BaseModel):
    """厂商适配层唯一需要转换的对话响应形状。"""

    model_config = ConfigDict(extra="ignore")

    text: str = Field(min_length=1)


class ResilientChatGateway:
    """对注入 transport 做超时、一次重试和结构校验。"""

    def __init__(
        self,
        transport: ChatTransport,
        *,
        timeout_seconds: float = 5.0,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self._transport = transport
        self._timeout_seconds = timeout_seconds
        self._sleeper = sleeper

    def generate(self, request: ChatGatewayRequest) -> ChatGatewayResult:
        failure_code = "GATEWAY_UNAVAILABLE"
        for attempt in range(1, 3):
            try:
                raw_response = self._transport(request, self._timeout_seconds)
                provider_response = ProviderChatResponse.model_validate(raw_response)
                filtered_text = filter_sensitive_text(provider_response.text)
                if not filtered_text.strip():
                    failure_code = "EMPTY_RESPONSE"
                    raise ValueError(failure_code)
                return ChatGatewayResult(
                    text=filtered_text,
                    status="success",
                    source="integrated",
                    attempts=attempt,
                )
            except TimeoutError:
                failure_code = "GATEWAY_TIMEOUT"
            except OSError:
                failure_code = "GATEWAY_UNAVAILABLE"
            except (ValidationError, ValueError):
                if failure_code == "GATEWAY_UNAVAILABLE":
                    failure_code = "INVALID_RESPONSE"
            if attempt == 1:
                self._sleeper(0)
        logger.warning("chat_gateway_failed code=%s attempts=2", failure_code)
        return ChatGatewayResult(
            status="degraded",
            source="degraded",
            attempts=2,
            failure_code=failure_code,
        )


class StaticChatGateway:
    """固定可重复的演示替身。"""

    def __init__(self, text: str) -> None:
        self._text = text

    def generate(self, request: ChatGatewayRequest) -> ChatGatewayResult:
        return ChatGatewayResult(
            text=filter_sensitive_text(self._text),
            status="success",
            source="demo",
            attempts=1,
        )


class UnconfiguredChatGateway:
    """未配置集成时的稳定降级。"""

    def generate(self, request: ChatGatewayRequest) -> ChatGatewayResult:
        return ChatGatewayResult(
            status="degraded",
            source="unconfigured",
            attempts=0,
            failure_code="INTEGRATION_UNAVAILABLE",
        )


class FallbackChatGateway:
    """主网关失败后切换到固定替身或未配置降级。"""

    def __init__(self, primary: ChatGateway, fallback: ChatGateway) -> None:
        self._primary = primary
        self._fallback = fallback

    def generate(self, request: ChatGatewayRequest) -> ChatGatewayResult:
        primary_result = self._primary.generate(request)
        if primary_result.status == "success":
            return primary_result
        fallback_result = self._fallback.generate(request)
        return fallback_result.model_copy(
            update={"failure_code": primary_result.failure_code}
        )


def create_configured_chat_gateway() -> ChatGateway:
    """从后端环境变量创建 DeepSeek 网关；缺少密钥时稳定降级。"""
    api_key = os.getenv("CANVAS_AGENT_LLM_API_KEY", "").strip()
    if not api_key:
        return UnconfiguredChatGateway()

    base_url = os.getenv(
        "CANVAS_AGENT_LLM_BASE_URL",
        "https://api.deepseek.com/v1",
    ).strip()
    model = os.getenv("CANVAS_AGENT_LLM_MODEL", "deepseek-v4-flash").strip()
    if not base_url or not model:
        return UnconfiguredChatGateway()
    timeout_raw = os.getenv("CANVAS_AGENT_LLM_TIMEOUT_SECONDS", "20").strip()
    try:
        timeout_seconds = max(1.0, min(float(timeout_raw), 120.0))
    except ValueError:
        timeout_seconds = 20.0

    return FallbackChatGateway(
        ResilientChatGateway(
            OpenAICompatibleChatTransport(
                api_key=api_key,
                base_url=base_url,
                model=model,
            ),
            timeout_seconds=timeout_seconds,
        ),
        UnconfiguredChatGateway(),
    )


def filter_sensitive_text(text: str) -> str:
    """过滤常见邮箱、手机号和 Bearer 凭证，避免进入候选文案。"""
    filtered = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[已过滤邮箱]", text)
    filtered = re.sub(r"(?<!\d)1[3-9]\d{9}(?!\d)", "[已过滤手机号]", filtered)
    filtered = re.sub(
        r"Bearer\s+[^\s]+", "Bearer [已过滤凭证]", filtered, flags=re.IGNORECASE
    )
    return re.sub(
        r"(姓名|学号|教学班|班级|掌握度|学习画像)\s*[:：]\s*[^\s,，。；;]+",
        r"\1：[已过滤身份信息]",
        filtered,
    )
