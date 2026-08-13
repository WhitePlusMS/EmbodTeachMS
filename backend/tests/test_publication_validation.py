import tempfile
import time
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.teaching_classes.publication import PublicationModule
from tests.conftest import build_app, seed_preparation_state
from app.auth.models import UserView


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


def test_publication_validation_success():
    """测试发布验证成功场景"""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        app, database = build_app(
            database_path=Path(tmpdir) / "test.db",
            jwt_secret="test-secret-with-enough-length",
        )

        with TestClient(app) as client:
            teacher_headers = register_user(client, "teacher_pub_valid")

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

            # 模拟解析完成状态
            with database.connect() as connection:
                seed_preparation_state(connection, session_id, questions=[{
                        "id": "question-1",
                        "source": "manual",
                        "review_status": "confirmed",
                        "type": "single_choice",
                        "stem": "测试题目",
                        "options": ["是", "否"],
                        "answers": [0],
                        "knowledge_points": ["测试"],
                        "highlight_source_ids": [],
                        "hint": "",
                        "explanation": "",
                        "created_at": int(time.time()),
                        "updated_at": int(time.time()),
                    }],
                current_step="questioning",
                )

            # 创建题目审核模块
            publication_module = app.state.publication_module

            # 获取教师信息并创建UserView
            teacher_response = client.get("/api/auth/me", headers=teacher_headers)
            teacher_dict = teacher_response.json()["data"]
            teacher = UserView(
                id=teacher_dict["id"],
                username=teacher_dict["username"],
                display_name=teacher_dict["displayName"],
                role=teacher_dict["role"]
            )

            # 测试验证成功
            session, questions = publication_module.validate_publication_conditions(
                class_id, teacher
            )

            assert session.id == session_id
            assert session.class_id == class_id
            assert session.parse_status.value == "completed"
            assert session.current_step.value in ["questioning", "publishing"]


def test_publication_validation_session_not_found():
    """测试会话不存在时的验证失败"""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        app = create_app(
            database_path=Path(tmpdir) / "test.db",
            jwt_secret="test-secret-with-enough-length",
        )

        with TestClient(app) as client:
            teacher_headers = register_user(client, "teacher_pub_not_found")

            # 创建教学班
            response = client.post(
                "/api/teaching-classes",
                headers=teacher_headers,
                json={"name": "测试教学班", "joinPolicy": "free"},
            )
            assert response.status_code == 201
            class_id = response.json()["data"]["id"]

            publication_module = app.state.publication_module

            teacher_response = client.get("/api/auth/me", headers=teacher_headers)
            teacher_dict = teacher_response.json()["data"]
            teacher = UserView(
                id=teacher_dict["id"],
                username=teacher_dict["username"],
                display_name=teacher_dict["displayName"],
                role=teacher_dict["role"]
            )

            # 测试会话不存在
            from app.common.errors import BusinessError
            from fastapi import HTTPException

            try:
                publication_module.validate_publication_conditions(
                    class_id, teacher
                )
                assert False, "应该抛出异常"
            except BusinessError as e:
                assert e.status_code == 404
                assert e.code == "PREPARATION_SESSION_NOT_FOUND"


def test_publication_validation_not_parsed():
    """测试未解析完成时的验证失败"""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        app, database = build_app(
            database_path=Path(tmpdir) / "test.db",
            jwt_secret="test-secret-with-enough-length",
        )

        with TestClient(app) as client:
            teacher_headers = register_user(client, "teacher_pub_not_parsed")

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

            # 保持未解析状态
            with database.connect() as connection:
                connection.execute(
                    """
                    UPDATE preparation_sessions
                    SET parse_status = 'not_started', current_step = 'upload',
                        published_at = NULL
                    WHERE id = ?
                    """,
                    (session_id,),
                )

            publication_module = app.state.publication_module

            teacher_response = client.get("/api/auth/me", headers=teacher_headers)
            teacher_dict = teacher_response.json()["data"]
            teacher = UserView(
                id=teacher_dict["id"],
                username=teacher_dict["username"],
                display_name=teacher_dict["displayName"],
                role=teacher_dict["role"]
            )

            # 测试未解析完成
            from app.common.errors import BusinessError

            try:
                publication_module.validate_publication_conditions(
                    class_id, teacher
                )
                assert False, "应该抛出异常"
            except BusinessError as e:
                assert e.status_code == 400
                assert e.code == "PREPARATION_SESSION_NOT_PARSED"


def test_publication_validation_already_published():
    """测试已发布时的幂等性验证"""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        app, database = build_app(
            database_path=Path(tmpdir) / "test.db",
            jwt_secret="test-secret-with-enough-length",
        )

        with TestClient(app) as client:
            teacher_headers = register_user(client, "teacher_pub_already")

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

            # 模拟已发布状态
            with database.connect() as connection:
                connection.execute(
                    """
                    UPDATE preparation_sessions
                    SET parse_status = 'completed', current_step = 'publishing',
                        published_at = ?
                    WHERE id = ?
                    """,
                    (int(time.time()), session_id),
                )

            publication_module = app.state.publication_module

            teacher_response = client.get("/api/auth/me", headers=teacher_headers)
            teacher_dict = teacher_response.json()["data"]
            teacher = UserView(
                id=teacher_dict["id"],
                username=teacher_dict["username"],
                display_name=teacher_dict["displayName"],
                role=teacher_dict["role"]
            )

            # 测试已发布
            from app.common.errors import BusinessError

            try:
                publication_module.validate_publication_conditions(
                    class_id, teacher
                )
                assert False, "应该抛出异常"
            except BusinessError as e:
                assert e.status_code == 409
                assert e.code == "PUBLICATION_ALREADY_EXISTS"


def test_publication_mark_completed():
    """测试标记发布完成功能"""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        app, database = build_app(
            database_path=Path(tmpdir) / "test.db",
            jwt_secret="test-secret-with-enough-length",
        )

        with TestClient(app) as client:
            teacher_headers = register_user(client, "teacher_pub_mark")

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

            course_content_ids = ["content_1", "content_2", "content_3"]

            # 测试标记发布完成
            with database.connect() as connection:
                publication_module.mark_publication_completed(
                    connection, session_id, course_content_ids
                )

            # 验证状态更新
            with database.connect() as connection:
                row = connection.execute(
                    "SELECT published_at, current_step FROM preparation_sessions WHERE id = ?",
                    (session_id,),
                ).fetchone()

                assert row is not None
                assert row["published_at"] is not None
                assert row["current_step"] == "publishing"
