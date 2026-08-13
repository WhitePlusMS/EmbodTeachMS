"""小D伴学 chat 端点的 HTTP 测试，应答经由 LLM 集成骨架 seam。"""

import time
import uuid
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.llm_gateway import (
    ChatGatewayResult,
    FallbackChatGateway,
    ResilientChatGateway,
    StaticChatGateway,
    UnconfiguredChatGateway,
)
from app.llm_gateway.router import XIAOD_DEGRADED_TEXT
from app.main import create_app
from tests.conftest import build_app


def register(client: TestClient, username: str, role: str = "learner") -> dict[str, str]:
    response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "StrongPass123!",
            "displayName": username,
            "role": role,
        },
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['data']['accessToken']}"}


def ask(
    client: TestClient,
    headers: dict[str, str],
    class_id: str = "class-1",
    content_id: str = "content-1",
):
    return client.post(
        "/api/xiaod/chat",
        headers=headers,
        json={
            "classId": class_id,
            "contentId": content_id,
            "question": "为什么机械臂需要反馈控制？",
            "mode": "explain",
        },
    )


def create_chat_context(client: TestClient, database) -> tuple[dict[str, str], str, str]:
    teacher = register(client, "xiaod_context_teacher", "teacher")
    learner = register(client, "xiaod_context_learner")
    class_id = client.post(
        "/api/teaching-classes",
        headers=teacher,
        json={"name": "小D上下文班", "joinPolicy": "free"},
    ).json()["data"]["id"]
    assert client.post(
        f"/api/teaching-classes/{class_id}/join", headers=learner
    ).status_code == 201
    content_id = str(uuid.uuid4())
    now = int(time.time())
    with database.connect() as connection:
        connection.execute(
            """
            INSERT INTO course_contents (
                id, class_id, content_type, publication_status,
                title, content, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                content_id,
                class_id,
                "knowledge_module",
                "published",
                "反馈控制",
                "反馈控制根据目标值与实际输出的误差调整执行器。",
                now,
                now,
            ),
        )
    return learner, class_id, content_id


def test_xiaod_chat_unconfigured_returns_stable_degraded(tmp_path: Path) -> None:
    app = create_app(
        database_path=tmp_path / "xiaod-unconfigured.db",
        jwt_secret="test-secret-with-enough-length",
    )
    with TestClient(app) as client:
        learner = register(client, "xiaod_learner")
        response = ask(client, learner)
        assert response.status_code == 200
        assert response.json()["code"] == "XIAOD_CHAT_COMPLETED"
        data = response.json()["data"]
        assert data["status"] == "degraded"
        assert data["source"] == "unconfigured"
        assert data["failureCode"] == "INTEGRATION_UNAVAILABLE"
        assert data["text"] == XIAOD_DEGRADED_TEXT


def test_xiaod_chat_success_and_fallback_keep_source_visible(tmp_path: Path) -> None:
    app, database = build_app(
        tmp_path / "xiaod-gateway.db",
        jwt_secret="test-secret-with-enough-length",
    )
    with TestClient(app) as client:
        learner, class_id, content_id = create_chat_context(client, database)

        app.state.xiaod_chat_gateway = StaticChatGateway("先看传感器的读数，再调整增益。")
        answered = ask(client, learner, class_id, content_id).json()["data"]
        assert answered["status"] == "success"
        assert answered["source"] == "demo"
        assert answered["text"] == "先看传感器的读数，再调整增益。"

        def timeout_transport(_request, _timeout):
            raise TimeoutError("gateway timeout")

        app.state.xiaod_chat_gateway = FallbackChatGateway(
            ResilientChatGateway(timeout_transport),
            UnconfiguredChatGateway(),
        )
        timed_out = ask(client, learner, class_id, content_id).json()["data"]
        assert timed_out["status"] == "degraded"
        assert timed_out["source"] == "unconfigured"
        assert timed_out["failureCode"] == "GATEWAY_TIMEOUT"
        assert timed_out["text"] == XIAOD_DEGRADED_TEXT


def test_injected_gateway_is_shared_with_xiaod_route(tmp_path: Path) -> None:
    app, database = build_app(
        tmp_path / "xiaod-injected.db",
        jwt_secret="test-secret-with-enough-length",
        chat_gateway=StaticChatGateway("真实网关接缝已接通。"),
    )
    with TestClient(app) as client:
        learner, class_id, content_id = create_chat_context(client, database)
        answered = ask(client, learner, class_id, content_id).json()["data"]
        assert answered["status"] == "success"
        assert answered["source"] == "demo"
        assert answered["text"] == "真实网关接缝已接通。"


def test_xiaod_chat_flattens_multi_level_knowledge_references(tmp_path: Path) -> None:
    """知识库标题路径是数组时，小D仍应返回可展示的字符串引用而非 500。"""
    app, database = build_app(
        tmp_path / "xiaod-nested-references.db",
        jwt_secret="test-secret-with-enough-length",
    )

    class StubKnowledgeBaseService:
        def search_for_class_member(self, **_kwargs):
            return SimpleNamespace(results=[SimpleNamespace(title_path=["长版课程正文", "跟踪与状态更新"], content="检索内容")])

    class IntegratedStaticGateway:
        def generate(self, _request):
            return ChatGatewayResult(
                text="已根据课程资料回答。",
                status="success",
                source="integrated",
                attempts=1,
            )

    with TestClient(app) as client:
        learner, class_id, content_id = create_chat_context(client, database)
        app.state.knowledge_base_service = StubKnowledgeBaseService()
        app.state.xiaod_chat_gateway = IntegratedStaticGateway()

        response = ask(client, learner, class_id, content_id)

        assert response.status_code == 200
        assert response.json()["data"]["references"] == ["长版课程正文 / 跟踪与状态更新"]


def test_xiaod_chat_requires_login(tmp_path: Path) -> None:
    app = create_app(
        database_path=tmp_path / "xiaod-auth.db",
        jwt_secret="test-secret-with-enough-length",
    )
    with TestClient(app) as client:
        response = client.post(
            "/api/xiaod/chat",
            json={"classId": "c1", "contentId": "k1", "question": "问题"},
        )
        assert response.status_code == 401
