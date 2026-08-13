"""课程概述候选调用链 HTTP 测试。"""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.llm_gateway import (
    ChatGateway,
    ChatGatewayRequest,
    ChatGatewayResult,
    FallbackChatGateway,
    ResilientChatGateway,
    StaticChatGateway,
    UnconfiguredChatGateway,
)
from app.main import create_app


class MutableChatGateway:
    """测试专用网关：内部实现可替换，用于经构造注入后切换场景。"""

    def __init__(self, inner: ChatGateway) -> None:
        self.inner = inner

    def generate(self, request: ChatGatewayRequest) -> ChatGatewayResult:
        return self.inner.generate(request)


def register(client: TestClient, username: str, role: str) -> dict[str, str]:
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


def create_class(client: TestClient, headers: dict[str, str], name: str) -> str:
    response = client.post(
        "/api/teaching-classes",
        headers=headers,
        json={"name": name, "joinPolicy": "free"},
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def candidate_text() -> str:
    return json.dumps(
        {
            "background": "机器人运动控制基础",
            "introduction": "从传感器到执行器建立实践闭环。",
            "objectives": "能够解释反馈控制并完成基础调试。",
            "features": "强调可观察的课堂实践证据。",
        },
        ensure_ascii=False,
    )


def test_candidates_require_teacher_and_adoption_is_explicit(tmp_path: Path) -> None:
    app = create_app(
        database_path=tmp_path / "overview-candidates.db",
        jwt_secret="test-secret-with-enough-length",
        chat_gateway=StaticChatGateway(candidate_text()),
    )
    with TestClient(app) as client:
        teacher = register(client, "candidate_teacher", "teacher")
        other_teacher = register(client, "candidate_other_teacher", "teacher")
        learner = register(client, "candidate_learner", "learner")
        class_id = create_class(client, teacher, "候选课程班")
        other_class_id = create_class(client, other_teacher, "其他候选班")

        before = client.get(
            f"/api/teaching-classes/{class_id}/course-overview", headers=teacher
        ).json()["data"]
        generated = client.post(
            f"/api/teaching-classes/{class_id}/course-overview/candidates",
            headers=teacher,
        )
        assert generated.status_code == 200
        assert generated.json()["code"] == "COURSE_OVERVIEW_CANDIDATES_GENERATED"
        candidate = generated.json()["data"]
        assert candidate["source"] == "demo"
        assert candidate["status"] == "success"
        assert candidate["background"] == "机器人运动控制基础"
        assert client.get(
            f"/api/teaching-classes/{class_id}/course-overview", headers=teacher
        ).json()["data"] == before

        adopted = client.put(
            f"/api/teaching-classes/{class_id}/course-overview",
            headers=teacher,
            json={key: candidate[key] for key in ("background", "introduction", "objectives", "features")},
        )
        assert adopted.status_code == 200
        assert adopted.json()["data"]["background"] == "机器人运动控制基础"

        assert client.post(
            f"/api/teaching-classes/{other_class_id}/course-overview/candidates",
            headers=teacher,
        ).status_code == 404
        assert client.post(
            f"/api/teaching-classes/{class_id}/course-overview/candidates",
            headers=learner,
        ).status_code == 403


def test_candidates_unconfigured_timeout_and_invalid_structure_are_explicit(tmp_path: Path) -> None:
    gateway = MutableChatGateway(UnconfiguredChatGateway())
    app = create_app(
        database_path=tmp_path / "overview-candidate-fallback.db",
        jwt_secret="test-secret-with-enough-length",
        chat_gateway=gateway,
    )
    with TestClient(app) as client:
        teacher = register(client, "fallback_candidate_teacher", "teacher")
        class_id = create_class(client, teacher, "降级候选班")
        endpoint = f"/api/teaching-classes/{class_id}/course-overview/candidates"

        unconfigured = client.post(endpoint, headers=teacher)
        assert unconfigured.status_code == 200
        assert unconfigured.json()["data"]["source"] == "unconfigured"
        assert unconfigured.json()["data"]["status"] == "degraded"

        def timeout_transport(_request, _timeout):
            raise TimeoutError("gateway timeout")

        gateway.inner = FallbackChatGateway(
            ResilientChatGateway(timeout_transport),
            UnconfiguredChatGateway(),
        )
        timed_out = client.post(endpoint, headers=teacher)
        assert timed_out.json()["data"]["source"] == "unconfigured"
        assert timed_out.json()["data"]["status"] == "degraded"

        gateway.inner = StaticChatGateway("不是 JSON")
        invalid = client.post(endpoint, headers=teacher)
        assert invalid.json()["data"]["source"] == "degraded"
        assert invalid.json()["data"]["status"] == "degraded"
        assert invalid.json()["data"]["background"]
