"""学习者课程内容详情 completed 字段 HTTP 测试。"""

import time
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from tests.conftest import build_app


def register_user(client: TestClient, username: str, role: str) -> dict[str, str]:
    """辅助函数：注册用户并返回认证头信息"""
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


def create_class_with_content(client: TestClient, database) -> tuple[dict[str, str], str, str]:
    """辅助函数：创建教师、学习者、教学班并发布一条课程内容"""
    teacher = register_user(client, f"teacher_{uuid.uuid4().hex[:8]}", "teacher")
    learner = register_user(client, f"learner_{uuid.uuid4().hex[:8]}", "learner")

    class_response = client.post(
        "/api/teaching-classes",
        headers=teacher,
        json={"name": "完成状态测试班", "joinPolicy": "free"},
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
            (content_id, class_id, "完成状态测试内容", "正文", now, now),
        )
    return learner, class_id, content_id


def get_detail(client: TestClient, learner: dict[str, str], class_id: str, content_id: str) -> dict:
    """辅助函数：学习者获取课程内容详情"""
    response = client.get(
        f"/api/teaching-classes/{class_id}/published-contents/{content_id}/learner",
        headers=learner,
    )
    assert response.status_code == 200
    assert response.json()["code"] == "PUBLISHED_CONTENT_DETAIL_FETCHED"
    return response.json()["data"]


def test_content_detail_completed_false_without_completion(tmp_path: Path) -> None:
    """未完成课程内容的学习者，详情返回 completed=false"""
    app, database = build_app(
        database_path=tmp_path / "detail_completed_false.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        learner, class_id, content_id = create_class_with_content(client, database)

        detail = get_detail(client, learner, class_id, content_id)
        assert detail["id"] == content_id
        assert detail["completed"] is False


def test_content_detail_completed_true_after_mark_complete(tmp_path: Path) -> None:
    """已标记完成的学习者再次进入详情，返回 completed=true"""
    app, database = build_app(
        database_path=tmp_path / "detail_completed_true.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        learner, class_id, content_id = create_class_with_content(client, database)

        # 学习者标记内容完成
        complete_response = client.post(
            f"/api/teaching-classes/{class_id}/contents/{content_id}/complete",
            headers=learner,
        )
        assert complete_response.status_code == 201

        # 重新进入详情时应反映真实完成状态
        detail = get_detail(client, learner, class_id, content_id)
        assert detail["completed"] is True


def test_content_detail_completed_is_scoped_to_current_learner(tmp_path: Path) -> None:
    """完成状态按学习者隔离：他人完成不影响当前学习者的 completed"""
    app, database = build_app(
        database_path=tmp_path / "detail_completed_scoped.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        learner, class_id, content_id = create_class_with_content(client, database)
        other_learner = register_user(client, f"learner_{uuid.uuid4().hex[:8]}", "learner")
        join_response = client.post(
            f"/api/teaching-classes/{class_id}/join",
            headers=other_learner,
        )
        assert join_response.status_code == 201

        # 第一名学习者标记完成
        complete_response = client.post(
            f"/api/teaching-classes/{class_id}/contents/{content_id}/complete",
            headers=learner,
        )
        assert complete_response.status_code == 201

        # 第二名学习者查看同一内容仍为未完成
        detail = get_detail(client, other_learner, class_id, content_id)
        assert detail["completed"] is False
