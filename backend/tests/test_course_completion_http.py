"""学习者课程完成与首页汇总 HTTP 测试。"""

import time
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from tests.conftest import build_app


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
    return {
        "Authorization": f"Bearer {data['accessToken']}",
        "user_id": data["user"]["id"],
    }


def create_class_with_content(client: TestClient, database, tmp_path: Path) -> tuple[dict[str, str], dict[str, str], str, str]:
    teacher = register_user(client, f"teacher_{uuid.uuid4().hex[:8]}", "teacher")
    learner = register_user(client, f"learner_{uuid.uuid4().hex[:8]}", "learner")
    class_response = client.post(
        "/api/teaching-classes",
        headers=teacher,
        json={"name": "完成测试班", "joinPolicy": "free"},
    )
    assert class_response.status_code == 201
    class_id = class_response.json()["data"]["id"]
    join_response = client.post(
        f"/api/teaching-classes/{class_id}/join",
        headers=learner,
    )
    assert join_response.status_code == 201

    content_id = str(uuid.uuid4())
    now = int(time.time())
    with database.connect() as connection:
        connection.execute(
            """
            INSERT INTO course_contents
              (id, class_id, content_type, publication_status, title, content, created_at, updated_at)
            VALUES (?, ?, 'knowledge_module', 'published', ?, ?, ?, ?)
            """,
            (content_id, class_id, "完成测试内容", "正文", now, now),
        )
    return teacher, learner, class_id, content_id


def test_mark_content_complete_is_idempotent_and_refreshes_summary(tmp_path: Path) -> None:
    app, database = build_app(database_path=tmp_path / "completion.db", jwt_secret="test-secret-with-enough-length")
    with TestClient(app) as client:
        _, learner, class_id, content_id = create_class_with_content(client, database, tmp_path)
        endpoint = f"/api/teaching-classes/{class_id}/contents/{content_id}/complete"

        first = client.post(endpoint, headers=learner)
        second = client.post(endpoint, headers=learner)

        assert first.status_code == 201
        assert second.status_code == 201
        assert first.json()["data"]["id"] == second.json()["data"]["id"]

        summary = client.get(
            f"/api/teaching-classes/{class_id}/home-summary",
            headers=learner,
        )
        assert summary.status_code == 200
        summary_data = summary.json()["data"]
        assert summary_data["completionStats"] == {
            "totalContents": 1,
            "completedContents": 1,
            "completionRate": 1.0,
        }
        assert summary_data["nextContent"] is None
        assert summary_data["masterySummary"]["status"] == "success"


def test_non_member_cannot_mark_or_read_summary(tmp_path: Path) -> None:
    app, database = build_app(database_path=tmp_path / "completion-permission.db", jwt_secret="test-secret-with-enough-length")
    with TestClient(app) as client:
        _, _, class_id, content_id = create_class_with_content(client, database, tmp_path)
        outsider = register_user(client, f"outsider_{uuid.uuid4().hex[:8]}", "learner")

        complete = client.post(
            f"/api/teaching-classes/{class_id}/contents/{content_id}/complete",
            headers=outsider,
        )
        summary = client.get(
            f"/api/teaching-classes/{class_id}/home-summary",
            headers=outsider,
        )

        assert complete.status_code == 403
        assert summary.status_code == 403


def test_cannot_complete_unpublished_or_missing_content(tmp_path: Path) -> None:
    app, database = build_app(database_path=tmp_path / "completion-missing.db", jwt_secret="test-secret-with-enough-length")
    with TestClient(app) as client:
        _, learner, class_id, _ = create_class_with_content(client, database, tmp_path)
        missing = client.post(
            f"/api/teaching-classes/{class_id}/contents/{uuid.uuid4()}/complete",
            headers=learner,
        )
        assert missing.status_code == 404
