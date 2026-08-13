import json
from pathlib import Path
import logging

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

    def __init__(self, question_type: str = "single_choice") -> None:
        self.requests: list[ChatGatewayRequest] = []
        self.question_type = question_type

    def generate(self, request: ChatGatewayRequest) -> ChatGatewayResult:
        self.requests.append(request)
        context = json.loads(request.input_text)
        highlight_ids = [item["id"] for item in context["highlights"]]
        items = [
            {
                "type": self.question_type,
                "stem": f"第 {index + 1} 道重点题是什么？",
                "options": ["传感", "猜测"],
                "answers": [0] if self.question_type == "single_choice" else [0, 1],
                "knowledgePoints": ["具身智能案例"],
                "highlightSourceIds": [highlight_ids[index % len(highlight_ids)]],
                "hint": "查看重点",
                "explanation": "重点来自教师标注。",
            }
            for index in range(context["questionCount"])
        ]
        return ChatGatewayResult(
            text=json.dumps({"items": items}, ensure_ascii=False),
            status="success",
            source="demo",
            attempts=1,
        )


class InvalidCandidateGateway:
    """返回成功状态但内容不是 JSON 的模型替身。"""

    def generate(self, request: ChatGatewayRequest) -> ChatGatewayResult:
        return ChatGatewayResult(
            text="不是 JSON",
            status="success",
            source="integrated",
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


def _candidate_request(highlight_ids: list[str], question_count: int = 1) -> dict[str, object]:
    return {"highlightIds": highlight_ids, "questionCount": question_count}


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
            json=_candidate_request(["missing-highlight"]),
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
        highlight_id = highlighted.json()["data"]["id"]

        generated = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/questions/candidates",
            headers=headers,
            json=_candidate_request([highlight_id]),
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
            json=_candidate_request([highlight_id]),
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
        highlighted = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/highlights",
            headers=headers,
            json={"paragraphOrdinal": 1, "startOffset": 0, "endOffset": 4},
        )
        assert highlighted.status_code == 201
        highlight_id = highlighted.json()["data"]["id"]

        generated = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/questions/candidates",
            headers=headers,
            json=_candidate_request([highlight_id]),
        )
        assert generated.status_code == 200
        assert generated.json()["data"]["source"] == "demo"
        request = gateway.requests[-1]
        context = json.loads(request.input_text)
        assert "小A" in request.system_text
        assert "task" not in context
        assert context["questionCount"] == 1
        assert context["highlights"][0]["text"] == "传感器融"[:4]
        assert context["highlights"][0]["documentFilename"]


def test_invalid_candidate_payload_logs_diagnostic_reason(
    tmp_path: Path, caplog,
) -> None:
    app = create_app(
        database_path=tmp_path / "xiaoa_invalid_payload.db",
        jwt_secret="test-secret-with-enough-length",
        course_content_parsing=StubCourseContentParsing(),
        parsing_executor=lambda task: task(),
        chat_gateway=InvalidCandidateGateway(),
    )
    with TestClient(app) as client:
        headers = _teacher(client, "xiaoa_invalid_payload_teacher")
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
        highlighted = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/highlights",
            headers=headers,
            json={"paragraphOrdinal": 1, "startOffset": 0, "endOffset": 4},
        )
        assert highlighted.status_code == 201
        highlight_id = highlighted.json()["data"]["id"]

        caplog.set_level(logging.WARNING, logger="course_agent.teaching_classes.preparation_questions")
        generated = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/questions/candidates",
            headers=headers,
            json=_candidate_request([highlight_id]),
        )

        assert generated.status_code == 200
        assert generated.json()["data"]["status"] == "degraded"
        diagnostic_logs = "\n".join(
            record.getMessage()
            for record in caplog.records
            if "[candidate-question-diagnostics]" in record.getMessage()
        )
        assert "failure_kind=invalid_json" in diagnostic_logs
        assert "response_preview='不是 JSON'" in diagnostic_logs


def test_candidate_generation_uses_selected_highlights_and_requested_count(tmp_path: Path) -> None:
    gateway = CandidateRecordingGateway()
    app = create_app(
        database_path=tmp_path / "xiaoa_selected_highlights.db",
        jwt_secret="test-secret-with-enough-length",
        course_content_parsing=StubCourseContentParsing(),
        parsing_executor=lambda task: task(),
        chat_gateway=gateway,
    )
    with TestClient(app) as client:
        headers = _teacher(client, "xiaoa_selected_highlights_teacher")
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
        first = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/highlights",
            headers=headers,
            json={"paragraphOrdinal": 1, "startOffset": 0, "endOffset": 4},
        )
        second = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/highlights",
            headers=headers,
            json={"paragraphOrdinal": 1, "startOffset": 5, "endOffset": 7},
        )
        assert first.status_code == 201
        assert second.status_code == 201
        first_id = first.json()["data"]["id"]
        second_id = second.json()["data"]["id"]

        one_question = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/questions/candidates",
            headers=headers,
            json=_candidate_request([first_id, second_id], 1),
        )
        assert one_question.status_code == 200
        assert len(one_question.json()["data"]["items"]) == 1
        one_context = json.loads(gateway.requests[-1].input_text)
        assert one_context["questionCount"] == 1
        assert [item["id"] for item in one_context["highlights"]] == [first_id, second_id]

        two_questions = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/questions/candidates",
            headers=headers,
            json=_candidate_request([first_id, second_id], 2),
        )
        assert two_questions.status_code == 200
        assert len(two_questions.json()["data"]["items"]) == 2
        two_context = json.loads(gateway.requests[-1].input_text)
        assert two_context["questionCount"] == 2
        assert len(two_context["highlights"]) == 2
        assert all(
            item["type"] == "single_choice"
            for item in two_questions.json()["data"]["items"]
        )


def test_candidate_generation_rejects_multiple_choice_response(
    tmp_path: Path, caplog,
) -> None:
    gateway = CandidateRecordingGateway(question_type="multiple_choice")
    app = create_app(
        database_path=tmp_path / "xiaoa_multiple_choice.db",
        jwt_secret="test-secret-with-enough-length",
        course_content_parsing=StubCourseContentParsing(),
        parsing_executor=lambda task: task(),
        chat_gateway=gateway,
    )
    with TestClient(app) as client:
        headers = _teacher(client, "xiaoa_multiple_choice_teacher")
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
        highlighted = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/highlights",
            headers=headers,
            json={"paragraphOrdinal": 1, "startOffset": 0, "endOffset": 4},
        )
        assert highlighted.status_code == 201
        highlight_id = highlighted.json()["data"]["id"]

        caplog.set_level(logging.WARNING, logger="course_agent.teaching_classes.preparation_questions")
        generated = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/questions/candidates",
            headers=headers,
            json=_candidate_request([highlight_id]),
        )

        assert generated.status_code == 200
        assert generated.json()["data"]["status"] == "degraded"
        diagnostic_logs = "\n".join(
            record.getMessage()
            for record in caplog.records
            if "[candidate-question-diagnostics]" in record.getMessage()
        )
        assert "failure_kind=question_type_not_allowed" in diagnostic_logs
