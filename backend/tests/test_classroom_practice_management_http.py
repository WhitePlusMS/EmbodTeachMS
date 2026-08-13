"""教师课堂练习管理 HTTP 回归。"""

import time
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from tests.conftest import build_app, seed_preparation_state


def _register(client: TestClient, role: str, prefix: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/register",
        json={
            "username": f"{prefix}_{uuid.uuid4().hex[:8]}",
            "password": "StrongPass123!",
            "displayName": prefix,
            "role": role,
        },
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['data']['accessToken']}"}


def _prepare_confirmed_question(client: TestClient, database, headers: dict[str, str], class_id: str) -> None:
    response = client.post(
        f"/api/teaching-classes/{class_id}/preparation-session",
        headers=headers,
    )
    assert response.status_code == 201
    session_id = response.json()["data"]["id"]
    now = int(time.time())
    with database.connect() as connection:
        seed_preparation_state(
            connection,
            session_id,
            segments=[(1, "text", "机器人运动控制课程内容")],
            questions=[{
                        "id": str(uuid.uuid4()),
                        "source": "manual",
                        "review_status": "confirmed",
                        "type": "single_choice",
                        "stem": "机器人如何保持平衡？",
                        "options": ["反馈控制", "关闭传感器"],
                        "answers": [0],
                        "knowledge_points": ["运动控制"],
                        "highlight_source_ids": [],
                        "hint": "",
                        "explanation": "反馈控制可以修正姿态误差。",
                        "created_at": now,
                        "updated_at": now,
                    }],
            current_step="publishing",
        )


def test_teacher_practice_list_is_published_scoped_and_refreshable(tmp_path: Path) -> None:
    app, database = build_app(
        database_path=tmp_path / "teacher-practice-management.db",
        jwt_secret="test-secret-with-enough-length",
    )
    with TestClient(app) as client:
        teacher = _register(client, "teacher", "practice_teacher")
        other_teacher = _register(client, "teacher", "other_teacher")
        class_response = client.post(
            "/api/teaching-classes",
            headers=teacher,
            json={"name": "课堂练习管理班", "joinPolicy": "free"},
        )
        assert class_response.status_code == 201
        class_id = class_response.json()["data"]["id"]
        other_class_response = client.post(
            "/api/teaching-classes",
            headers=other_teacher,
            json={"name": "其他教师班", "joinPolicy": "free"},
        )
        assert other_class_response.status_code == 201
        other_class_id = other_class_response.json()["data"]["id"]

        _prepare_confirmed_question(client, database, teacher, class_id)
        before_publish = client.get(
            f"/api/teaching-classes/{class_id}/published-contents", headers=teacher
        )
        assert before_publish.status_code == 200
        assert before_publish.json()["data"]["items"] == []

        publish = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/publish",
            headers=teacher,
        )
        assert publish.status_code == 200
        published = client.get(
            f"/api/teaching-classes/{class_id}/published-contents", headers=teacher
        )
        assert published.status_code == 200
        question_items = [
            item for item in published.json()["data"]["items"]
            if item["contentType"] == "question"
        ]
        assert len(question_items) == 1
        assert "机器人如何保持平衡" in question_items[0]["content"]
        assert question_items[0]["question"]["knowledgePoints"] == ["运动控制"]

        refreshed = client.get(
            f"/api/teaching-classes/{class_id}/published-contents", headers=teacher
        )
        assert refreshed.json()["data"]["items"] == published.json()["data"]["items"]

        # 其他教师班级对当前教师表现为不可见资源，沿用 require_owned_class 的 404 契约。
        assert client.get(
            f"/api/teaching-classes/{other_class_id}/published-contents", headers=teacher
        ).status_code == 404
