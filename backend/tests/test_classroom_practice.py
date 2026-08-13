"""课件内课堂练习作答 HTTP 测试。"""

import time
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from tests.conftest import build_app
from tests.question_factory import insert_published_question


def register_user(client: TestClient, username: str, role: str) -> dict[str, str]:
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
    data = response.json()["data"]
    return {"Authorization": f"Bearer {data['accessToken']}"}


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
    teacher = register_user(client, f"teacher_{uuid.uuid4().hex[:8]}", "teacher")
    learner = register_user(client, f"learner_{uuid.uuid4().hex[:8]}", "learner")
    class_response = client.post(
        "/api/teaching-classes",
        headers=teacher,
        json={"name": "课堂练习测试班", "joinPolicy": "free"},
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
            title="课堂练习",
        )
    return learner, class_id, content_id


def test_single_choice_feedback_persists_after_refresh(tmp_path: Path) -> None:
    app, database = build_app(database_path=tmp_path / "single-practice.db", jwt_secret="test-secret-with-enough-length")
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
        detail = client.get(
            f"/api/teaching-classes/{class_id}/published-contents/{content_id}/practice-detail",
            headers=learner,
        )
        assert detail.status_code == 200
        assert detail.json()["data"]["attempt"] is None

        submitted = client.post(
            f"/api/teaching-classes/{class_id}/published-contents/{content_id}/submit-answer",
            headers=learner,
            json={"classId": class_id, "contentId": content_id, "selectedAnswers": [0]},
        )
        assert submitted.status_code == 201
        assert submitted.json()["data"]["isCorrect"] is True
        assert submitted.json()["data"]["correctAnswers"] == [0]

        refreshed = client.get(
            f"/api/teaching-classes/{class_id}/published-contents/{content_id}/practice-detail",
            headers=learner,
        )
        refreshed_data = refreshed.json()["data"]
        assert refreshed_data["attempt"]["selectedAnswers"] == [0]
        assert refreshed_data["correctAnswers"] == [0]
        assert refreshed_data["explanation"] == "基础加法"
        assert refreshed_data["content"]["completed"] is True

        repeated_submit = client.post(
            f"/api/teaching-classes/{class_id}/published-contents/{content_id}/submit-answer",
            headers=learner,
            json={"classId": class_id, "contentId": content_id, "selectedAnswers": [1]},
        )
        assert repeated_submit.status_code == 400
        assert repeated_submit.json()["code"] == "ATTEMPT_ALREADY_EXISTS"

        manual_complete = client.post(
            f"/api/teaching-classes/{class_id}/contents/{content_id}/complete",
            headers=learner,
        )
        assert manual_complete.status_code == 400
        assert manual_complete.json()["code"] == "CLASSROOM_PRACTICE_COMPLETION_REQUIRES_SUBMISSION"


def test_multiple_choice_requires_exact_answer_set_and_empty_is_rejected(tmp_path: Path) -> None:
    app, database = build_app(database_path=tmp_path / "multiple-practice.db", jwt_secret="test-secret-with-enough-length")
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
        endpoint = f"/api/teaching-classes/{class_id}/published-contents/{content_id}/submit-answer"
        empty = client.post(endpoint, headers=learner, json={"classId": class_id, "contentId": content_id, "selectedAnswers": []})
        assert empty.status_code == 400
        assert empty.json()["code"] == "NO_ANSWER_SELECTED"

        partial = client.post(endpoint, headers=learner, json={"classId": class_id, "contentId": content_id, "selectedAnswers": [0]})
        assert partial.status_code == 201
        assert partial.json()["data"]["isCorrect"] is False
        assert partial.json()["data"]["correctAnswers"] == [0, 1]


def test_non_member_cannot_access_or_submit_classroom_practice(tmp_path: Path) -> None:
    app, database = build_app(database_path=tmp_path / "practice-permission.db", jwt_secret="test-secret-with-enough-length")
    with TestClient(app) as client:
        learner, class_id, content_id = create_question(
            client,
            database,
            question_type="single_choice",
            stem="题目",
            options=["A"],
            correct_answers=[0],
        )
        outsider = register_user(client, f"outsider_{uuid.uuid4().hex[:8]}", "learner")
        detail = client.get(
            f"/api/teaching-classes/{class_id}/published-contents/{content_id}/practice-detail",
            headers=outsider,
        )
        submit = client.post(
            f"/api/teaching-classes/{class_id}/published-contents/{content_id}/submit-answer",
            headers=outsider,
            json={"classId": class_id, "contentId": content_id, "selectedAnswers": [0]},
        )
        assert detail.status_code == 403
        assert submit.status_code == 403
