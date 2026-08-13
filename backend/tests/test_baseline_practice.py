"""基准练习确定性状态机 HTTP 测试。"""

import time
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from tests.conftest import build_app
from tests.question_factory import insert_published_question


def register_user(client: TestClient, role: str) -> dict[str, str]:
    username = f"{role}_{uuid.uuid4().hex[:8]}"
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


def create_question(
    client: TestClient,
    database,
    *,
    question_type: str,
    stem: str,
    options: list[str],
    correct_answers: list[int],
    explanation: str = "",
) -> tuple[dict[str, str], str, str]:
    teacher = register_user(client, "teacher")
    learner = register_user(client, "learner")
    class_response = client.post(
        "/api/teaching-classes",
        headers=teacher,
        json={"name": "基准练习测试班", "joinPolicy": "free"},
    )
    assert class_response.status_code == 201
    class_id = class_response.json()["data"]["id"]
    assert client.post(f"/api/teaching-classes/{class_id}/join", headers=learner).status_code == 201

    with database.connect() as connection:
        content_id = insert_published_question(
            connection,
            class_id,
            question_type=question_type,
            stem=stem,
            options=options,
            correct_answers=correct_answers,
            explanation=explanation,
            title="基准练习",
        )
    return learner, class_id, content_id


def endpoint(class_id: str, content_id: str, action: str = "") -> str:
    suffix = f"/{action}" if action else ""
    return f"/api/teaching-classes/{class_id}/published-contents/{content_id}/baseline-practice{suffix}"


def test_wrong_answer_shows_one_prompt_then_second_attempt_completes(tmp_path: Path) -> None:
    app, database = build_app(database_path=tmp_path / "baseline-state.db", jwt_secret="test-secret-with-enough-length")
    with TestClient(app) as client:
        learner, class_id, content_id = create_question(
            client,
            database,
            question_type="single_choice",
            stem="1+1=?",
            options=["2", "3"],
            correct_answers=[0],
            explanation="基础加法",
        )
        detail = client.get(endpoint(class_id, content_id), headers=learner)
        assert detail.status_code == 200
        assert detail.json()["data"]["status"] == "initial"
        assert detail.json()["data"]["correctAnswers"] == []

        first = client.post(endpoint(class_id, content_id, "submit"), headers=learner, json={"selectedAnswers": [1]})
        assert first.status_code == 201
        assert first.json()["data"]["status"] == "prompt_shown"
        assert first.json()["data"]["hint"]
        assert first.json()["data"]["correctAnswers"] == []
        assert first.json()["data"]["explanation"] == ""

        second = client.post(endpoint(class_id, content_id, "submit"), headers=learner, json={"selectedAnswers": [0]})
        assert second.status_code == 201
        assert second.json()["data"]["status"] == "completed"
        assert second.json()["data"]["isCorrect"] is True

        terminal = client.post(endpoint(class_id, content_id, "submit"), headers=learner, json={"selectedAnswers": [0]})
        assert terminal.status_code == 400
        assert terminal.json()["code"] == "INVALID_STATUS"

        refreshed = client.get(endpoint(class_id, content_id), headers=learner)
        data = refreshed.json()["data"]
        assert data["status"] == "completed"
        assert data["firstAttemptAnswers"] == [1]
        assert data["secondAttemptAnswers"] == [0]
        assert data["correctAnswers"] == [0]
        assert data["resultType"] == "hint_correct"
        assert data["attemptQuality"] == 0.8


def test_first_correct_cannot_be_abandoned_and_multiple_choice_has_no_partial_credit(tmp_path: Path) -> None:
    app, database = build_app(database_path=tmp_path / "baseline-terminal.db", jwt_secret="test-secret-with-enough-length")
    with TestClient(app) as client:
        learner, class_id, content_id = create_question(
            client,
            database,
            question_type="multiple_choice",
            stem="质数",
            options=["2", "3", "4"],
            correct_answers=[0, 1],
            explanation="2 和 3 是质数",
        )
        partial = client.post(endpoint(class_id, content_id, "submit"), headers=learner, json={"selectedAnswers": [0]})
        assert partial.status_code == 201
        assert partial.json()["data"]["status"] == "prompt_shown"

        second_wrong = client.post(endpoint(class_id, content_id, "submit"), headers=learner, json={"selectedAnswers": [0, 2]})
        assert second_wrong.status_code == 201
        assert second_wrong.json()["data"]["isCorrect"] is False

        completed_abandon = client.post(endpoint(class_id, content_id, "abandon"), headers=learner)
        assert completed_abandon.status_code == 400
        assert completed_abandon.json()["code"] == "INVALID_STATUS"

        refreshed_completed = client.get(endpoint(class_id, content_id), headers=learner)
        assert refreshed_completed.json()["data"]["resultType"] == "final_wrong"
        assert refreshed_completed.json()["data"]["attemptQuality"] == 0.5

        # 独立验证主动结束路径，避免把已完成运行改写为 abandoned。
        second_learner, second_class_id, second_content_id = create_question(
            client,
            database,
            question_type="single_choice",
            stem="题目",
            options=["A", "B"],
            correct_answers=[0],
        )
        initial_abandon = client.post(endpoint(second_class_id, second_content_id, "abandon"), headers=second_learner)
        assert initial_abandon.status_code == 201
        assert initial_abandon.json()["data"]["status"] == "abandoned"

        repeated = client.post(endpoint(second_class_id, second_content_id, "abandon"), headers=second_learner)
        assert repeated.status_code == 201
        assert repeated.json()["data"]["status"] == "abandoned"

        third = client.post(endpoint(second_class_id, second_content_id, "submit"), headers=second_learner, json={"selectedAnswers": [0, 1]})
        assert third.status_code == 400
        assert third.json()["code"] == "INVALID_STATUS"


def test_empty_answer_and_non_member_are_rejected(tmp_path: Path) -> None:
    app, database = build_app(database_path=tmp_path / "baseline-permission.db", jwt_secret="test-secret-with-enough-length")
    with TestClient(app) as client:
        learner, class_id, content_id = create_question(
            client,
            database,
            question_type="single_choice",
            stem="题目",
            options=["A"],
            correct_answers=[0],
        )
        empty = client.post(endpoint(class_id, content_id, "submit"), headers=learner, json={"selectedAnswers": []})
        assert empty.status_code == 400
        assert empty.json()["code"] == "EMPTY_ANSWER"

        outsider = register_user(client, "learner")
        assert client.get(endpoint(class_id, content_id), headers=outsider).status_code == 403
        assert client.post(endpoint(class_id, content_id, "submit"), headers=outsider, json={"selectedAnswers": [0]}).status_code == 403
