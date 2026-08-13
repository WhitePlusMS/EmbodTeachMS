from pathlib import Path

from fastapi.testclient import TestClient

from app.teaching_classes.publication import PublicationModule
from tests.conftest import build_app


def register_user(client, username: str, role: str = "teacher") -> dict:
    """辅助函数：注册用户并返回认证头信息"""
    response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "StrongPass123!",
            "displayName": f"{username}老师",
            "role": role,
        },
    )
    assert response.status_code == 201
    data = response.json()["data"]
    return {"Authorization": f"Bearer {data['accessToken']}"}


def test_publication_status_management(tmp_path: Path):
    """测试发布状态管理功能"""
    app, database = build_app(
        database_path=tmp_path / "test.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_pub_status")

        # 创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={"name": "测试教学班", "joinPolicy": "free"},
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 创建备课会话
        response = client.post(f"/api/teaching-classes/{class_id}/preparation-session", headers=teacher_headers)
        assert response.status_code == 201
        session_id = response.json()["data"]["id"]

        publication_module = app.state.publication_module

        # 测试标记发布进行中
        course_content_ids = ["content_1", "content_2"]
        with database.connect() as connection:
            publication_module.mark_publication_in_progress(
                connection, session_id, course_content_ids
            )

        # 验证发布进行中状态
        with database.connect() as connection:
            row = connection.execute(
                "SELECT published_at FROM preparation_sessions WHERE id = ?",
                (session_id,),
            ).fetchone()

            assert row is not None
            assert row["published_at"] is None

        # 测试标记发布完成
        with database.connect() as connection:
            publication_module.mark_publication_completed(
                connection, session_id, course_content_ids
            )

        # 验证发布完成状态
        with database.connect() as connection:
            row = connection.execute(
                "SELECT published_at, current_step FROM preparation_sessions WHERE id = ?",
                (session_id,),
            ).fetchone()

            assert row is not None
            assert row["published_at"] is not None
            assert row["current_step"] == "publishing"

def test_publication_status_transitions(tmp_path: Path):
    """测试发布状态转换的完整性"""
    app, database = build_app(
        database_path=tmp_path / "test.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_pub_transitions")

        # 创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={"name": "测试教学班", "joinPolicy": "free"},
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 创建备课会话
        response = client.post(f"/api/teaching-classes/{class_id}/preparation-session", headers=teacher_headers)
        assert response.status_code == 201
        session_id = response.json()["data"]["id"]

        publication_module = app.state.publication_module

        # 完整的状态转换测试
        course_content_ids = ["content_1", "content_2", "content_3"]

        # 1. 初始状态
        with database.connect() as connection:
            row = connection.execute(
                "SELECT published_at, current_step FROM preparation_sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
            assert row["published_at"] is None
            assert row["current_step"] == "upload"

        # 2. 发布进行中
        with database.connect() as connection:
            publication_module.mark_publication_in_progress(
                connection, session_id, course_content_ids
            )

        # 3. 发布完成
        with database.connect() as connection:
            publication_module.mark_publication_completed(
                connection, session_id, course_content_ids
            )

        # 4. 验证最终状态
        with database.connect() as connection:
            row = connection.execute(
                "SELECT published_at, current_step FROM preparation_sessions WHERE id = ?",
                (session_id,),
            ).fetchone()

            assert row["published_at"] is not None
            assert row["current_step"] == "publishing"
