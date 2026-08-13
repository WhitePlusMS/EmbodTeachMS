"""小 B / 小 C 模型上下文、依赖注入与权限边界 HTTP 回归。"""

import json
import time
from pathlib import Path

from fastapi.testclient import TestClient

from app.llm_gateway import ChatGatewayRequest, ChatGatewayResult
from tests.conftest import build_app
from tests.test_teacher_homework_management_http import (
    create_class,
    join,
    register,
    seed_homework,
)


class TeacherAgentRecordingGateway:
    """按独立 system prompt 返回小 B / 小 C 严格 JSON，并保留请求证据。"""

    def __init__(self) -> None:
        self.requests: list[ChatGatewayRequest] = []

    def generate(self, request: ChatGatewayRequest) -> ChatGatewayResult:
        self.requests.append(request)
        if "小B" in request.system_text:
            payload = {"analysis": "班级当前样本较少。", "suggestions": ["继续积累学习事实。"]}
        elif "小C" in request.system_text:
            payload = {"analysis": "反馈控制题需要巩固。", "suggestions": ["复习反馈控制知识点。"]}
        else:
            raise AssertionError("unexpected teacher agent system prompt")
        return ChatGatewayResult(
            text=json.dumps(payload, ensure_ascii=False),
            status="success",
            source="demo",
            attempts=1,
        )


def test_teacher_agents_use_scoped_context_and_shared_gateway(tmp_path: Path) -> None:
    gateway = TeacherAgentRecordingGateway()
    app, database = build_app(
        database_path=tmp_path / "teacher-agent-ai.db",
        jwt_secret="test-secret-with-enough-length",
        chat_gateway=gateway,
    )
    with TestClient(app) as client:
        teacher, _ = register(client, "agent_ai_teacher", "teacher")
        other_teacher, _ = register(client, "agent_ai_other_teacher", "teacher")
        learner, learner_id = register(client, "agent_ai_learner", "learner")
        class_id = create_class(client, teacher, "AI 分析班")
        join(client, class_id, learner)
        homework_id, question_one_id, question_two_id = seed_homework(
            database, class_id, due_at=int(time.time()) + 3600
        )
        submitted = client.post(
            f"/api/teaching-classes/{class_id}/homework/{homework_id}/submit",
            headers=learner,
            json={
                "classId": class_id,
                "homeworkId": homework_id,
                "answers": {question_one_id: [0], question_two_id: [1]},
            },
        )
        assert submitted.status_code == 201

        xiaob = client.post(
            f"/api/teaching-classes/{class_id}/teacher-dashboard/ai-analysis",
            headers=teacher,
        )
        assert xiaob.status_code == 200
        assert xiaob.json()["data"]["source"] == "demo"
        xiaob_request = next(item for item in gateway.requests if "小B" in item.system_text)
        xiaob_context = json.loads(xiaob_request.input_text)
        assert xiaob_context["totalMembers"] == 1
        assert "learnerPreviews" not in xiaob_context
        assert learner_id not in xiaob_request.input_text

        xiaoc = client.get(
            f"/api/teaching-classes/{class_id}/homework/{homework_id}/ai-analysis/{learner_id}",
            headers=teacher,
        )
        assert xiaoc.status_code == 200
        assert xiaoc.json()["data"]["analysis"] == "反馈控制题需要巩固。"
        xiaoc_request = next(item for item in gateway.requests if "小C" in item.system_text)
        xiaoc_context = json.loads(xiaoc_request.input_text)
        assert xiaoc_context["questions"][0]["knowledgePoints"] == ["传感器"]
        assert xiaoc_context["questions"][1]["isCorrect"] is False
        assert learner_id not in xiaoc_request.input_text

        assert client.post(
            f"/api/teaching-classes/{class_id}/teacher-dashboard/ai-analysis",
            headers=other_teacher,
        ).status_code == 404
        assert client.get(
            f"/api/teaching-classes/{class_id}/homework/{homework_id}/ai-analysis/{learner_id}",
            headers=other_teacher,
        ).status_code == 404
