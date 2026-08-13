from pathlib import Path

from fastapi.testclient import TestClient

from app.document_parsing import CourseContentParsing
from app.document_parsing.models import ParsedParagraph, ParsingResult, ParsingStatus
from app.main import create_app
from app.llm_gateway import ChatGatewayRequest, ChatGatewayResult
from app.teaching_classes.models import FileFormat


class StubCourseContentParsing(CourseContentParsing):
    """返回固定解析结果的备课解析替身；配合同步执行器注入，替代 patch 内部实现 + time.sleep。"""

    def __init__(self) -> None:
        pass

    def parse(self, file_path: Path, file_format: FileFormat) -> ParsingResult:
        return ParsingResult(
            status=ParsingStatus.COMPLETED,
            paragraphs=[ParsedParagraph(order=1, block_type="paragraph", content="传感器融合是本节教学重点。")],
        )


class CandidateRecordingGateway:
    """记录 system/context，并根据真实重点 ID 返回严格候选题。"""

    def __init__(self) -> None:
        self.requests: list[ChatGatewayRequest] = []

    def generate(self, request: ChatGatewayRequest) -> ChatGatewayResult:
        self.requests.append(request)
        context = __import__("json").loads(request.input_text)
        highlight_id = context["highlights"][0]["id"]
        return ChatGatewayResult(
            text=__import__("json").dumps({
                "items": [{
                    "type": "single_choice",
                    "stem": "本节重点是什么？",
                    "options": ["传感", "猜测"],
                    "answers": [0],
                    "knowledgePoints": ["传感"],
                    "highlightSourceIds": [highlight_id],
                    "hint": "查看重点",
                    "explanation": "重点来自教师标注。",
                }],
            }, ensure_ascii=False),
            status="success",
            source="demo",
            attempts=1,
        )


def _teacher(client: TestClient, username: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "StrongPass123!",
            "displayName": username,
            "role": "teacher",
        },
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['data']['accessToken']}"}


def _class_and_session(client: TestClient, headers: dict[str, str]) -> str:
    created = client.post(
        "/api/teaching-classes",
        headers=headers,
        json={"name": "小A候选题班", "joinPolicy": "free"},
    )
    assert created.status_code == 201
    class_id = created.json()["data"]["id"]
    session = client.post(
        f"/api/teaching-classes/{class_id}/preparation-session",
        headers=headers,
    )
    assert session.status_code == 201
    return class_id


def test_candidate_generation_requires_highlights_and_keeps_review_gate(tmp_path: Path) -> None:
    app = create_app(
        database_path=tmp_path / "xiaoa_candidate.db",
        jwt_secret="test-secret-with-enough-length",
        course_content_parsing=StubCourseContentParsing(),
        parsing_executor=lambda task: task(),
    )
    with TestClient(app) as client:
        headers = _teacher(client, "xiaoa_teacher")
        class_id = _class_and_session(client, headers)

        no_highlight = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/questions/candidates",
            headers=headers,
        )
        assert no_highlight.status_code == 400
        assert no_highlight.json()["code"] == "NO_PREPARATION_HIGHLIGHTS"

        uploaded = client.put(
            f"/api/teaching-classes/{class_id}/preparation-session/upload",
            headers=headers,
            files={"file": ("lesson.md", b"# lesson")},
        )
        assert uploaded.status_code == 200
        # 同步执行器注入后，parse 响应返回时解析已完成，无需 sleep 等待后台线程
        parsed = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/parse",
            headers=headers,
        )
        assert parsed.status_code == 200

        highlighted = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/highlights",
            headers=headers,
            json={"paragraphOrdinal": 1, "startOffset": 0, "endOffset": 4},
        )
        assert highlighted.status_code == 201

        generated = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/questions/candidates",
            headers=headers,
        )
        assert generated.status_code == 200
        body = generated.json()["data"]
        assert body["source"] == "unconfigured"
        assert body["status"] == "degraded"
        assert body["items"] == []

        listed = client.get(
            f"/api/teaching-classes/{class_id}/preparation-session/questions",
            headers=headers,
        )
        assert listed.status_code == 200
        assert listed.json()["data"]["isPublishUnlocked"] is False
        assert listed.json()["data"]["items"] == []

        other_headers = _teacher(client, "xiaoa_other_teacher")
        denied = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/questions/candidates",
            headers=other_headers,
        )
        assert denied.status_code == 404


def test_candidate_prompt_separates_system_rules_from_highlight_context(tmp_path: Path) -> None:
    gateway = CandidateRecordingGateway()
    app = create_app(
        database_path=tmp_path / "xiaoa_prompt_context.db",
        jwt_secret="test-secret-with-enough-length",
        course_content_parsing=StubCourseContentParsing(),
        parsing_executor=lambda task: task(),
        chat_gateway=gateway,
    )
    with TestClient(app) as client:
        headers = _teacher(client, "xiaoa_prompt_teacher")
        class_id = _class_and_session(client, headers)
        assert client.put(
            f"/api/teaching-classes/{class_id}/preparation-session/upload",
            headers=headers,
            files={"file": ("lesson.md", b"# lesson")},
        ).status_code == 200
        assert client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/parse",
            headers=headers,
        ).status_code == 200
        assert client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/highlights",
            headers=headers,
            json={"paragraphOrdinal": 1, "startOffset": 0, "endOffset": 4},
        ).status_code == 201

        generated = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/questions/candidates",
            headers=headers,
        )
        assert generated.status_code == 200
        assert generated.json()["data"]["source"] == "demo"
        request = gateway.requests[-1]
        context = __import__("json").loads(request.input_text)
        assert "小A" in request.system_text
        assert "task" not in context
        assert context["highlights"][0]["text"] == "传感器融"[:4]
        assert context["highlights"][0]["documentFilename"]
