import json
import time
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from tests.conftest import build_app, seed_preparation_state


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


def test_publication_success(tmp_path: Path) -> None:
    """测试发布成功场景"""
    app, database = build_app(
        database_path=tmp_path / "publication_success.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_pub_success")

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

        # 模拟解析完成状态和题目条件
        with database.connect() as connection:
            highlights = [{
                "id": str(uuid.uuid4()),
                "paragraphOrdinal": 1,
                "startOffset": 0,
                "endOffset": 4,
                "createdAt": int(time.time())
            }]

            # 设置已确认的题目
            questions = [{
                "id": str(uuid.uuid4()),
                "source": "manual",
                "review_status": "confirmed",
                "type": "single_choice",
                "stem": "测试题目",
                "options": ["选项1", "选项2"],
                "answers": [0],
                "knowledge_points": ["知识点"],
                "highlight_source_ids": [],
                "hint": "提示",
                "explanation": "解析",
                "created_at": int(time.time()),
                "updated_at": int(time.time())
            }]

            seed_preparation_state(
                connection,
                session_id,
                segments=[(1, "text", "这是第一段内容"), (2, "text", "这是第二段内容")],
                highlights=highlights,
                questions=questions,
                current_step="publishing",
            )

        # 测试发布接口
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/publish",
            headers=teacher_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "PREPARATION_SESSION_PUBLISHED"
        assert data["message"] == "备课会话发布成功"

        # 验证发布状态
        session_data = data["data"]
        publication_draft = json.loads(session_data["publicationDraftJson"])
        assert publication_draft["published_at"] is not None
        assert len(publication_draft["course_content_ids"]) > 0

        # 验证课程内容已创建
        with database.connect() as connection:
            contents = connection.execute(
                "SELECT * FROM course_contents WHERE class_id = ?", (class_id,)
            ).fetchall()
        assert len(contents) == len(publication_draft["course_content_ids"])


def test_publication_session_not_found(tmp_path: Path) -> None:
    """测试会话不存在时的发布失败"""
    app = create_app(
        database_path=tmp_path / "pub_session_not_found.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_pub_not_found")

        # 创建教学班但不创建会话
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={"name": "测试教学班", "joinPolicy": "free"},
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 测试发布接口
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/publish",
            headers=teacher_headers
        )
        assert response.status_code == 404
        data = response.json()
        assert data["code"] == "PREPARATION_SESSION_NOT_FOUND"


def test_publication_not_parsed(tmp_path: Path) -> None:
    """测试未解析完成时的发布失败"""
    app, database = build_app(
        database_path=tmp_path / "pub_not_parsed.db",
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
                "UPDATE preparation_sessions SET parse_status = 'not_started' WHERE id = ?",
                (session_id,)
            )

        # 测试发布接口
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/publish",
            headers=teacher_headers
        )
        assert response.status_code == 400
        data = response.json()
        assert data["code"] == "PREPARATION_SESSION_NOT_PARSED"


def test_publication_already_published(tmp_path: Path) -> None:
    """测试已发布时的幂等性验证"""
    app, database = build_app(
        database_path=tmp_path / "pub_already.db",
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
            publication_draft = {
                "published_at": int(time.time()),
                "course_content_ids": ["content_1", "content_2"],
            }
            connection.execute(
                """
                UPDATE preparation_sessions
                SET parse_status = 'completed', current_step = 'publishing',
                    published_at = ?
                WHERE id = ?
                """,
                (publication_draft["published_at"], session_id)
            )

        # 测试发布接口
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/publish",
            headers=teacher_headers
        )
        assert response.status_code == 409
        data = response.json()
        assert data["code"] == "PUBLICATION_ALREADY_EXISTS"


def test_publication_cross_class_access(tmp_path: Path) -> None:
    """测试跨班访问权限验证"""
    app, database = build_app(
        database_path=tmp_path / "pub_cross_class.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        # 创建两个教师
        teacher1_headers = register_user(client, "teacher1_pub")
        teacher2_headers = register_user(client, "teacher2_pub")

        # 教师1创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher1_headers,
            json={"name": "教师1的教学班", "joinPolicy": "free"},
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 创建备课会话
        response = client.post(f"/api/teaching-classes/{class_id}/preparation-session", headers=teacher1_headers)
        assert response.status_code == 201
        session_id = response.json()["data"]["id"]

        # 模拟解析完成状态
        with database.connect() as connection:
            connection.execute(
                "UPDATE preparation_sessions SET parse_status = 'completed' WHERE id = ?",
                (session_id,)
            )

        # 教师2尝试发布教师1的会话
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/publish",
            headers=teacher2_headers
        )
        assert response.status_code == 404
        data = response.json()
        assert data["code"] == "RESOURCE_NOT_FOUND"


def test_publication_transaction_rollback(tmp_path: Path) -> None:
    """测试发布事务回滚"""
    app, database = build_app(
        database_path=tmp_path / "pub_rollback.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_pub_rollback")

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

        # 模拟解析完成状态，但设置无效的题目数据（会触发异常）
        with database.connect() as connection:
            connection.execute(
                """
                UPDATE preparation_sessions
                SET parse_status = 'completed', current_step = 'publishing',
                    published_at = NULL
                WHERE id = ?
                """,
                (session_id,)
            )
            connection.execute(
                """
                INSERT INTO preparation_questions(
                    id, session_id, source, review_status, question_type, stem,
                    options_json, correct_answers_json, knowledge_points_json,
                    highlight_source_ids_json, hint, explanation, created_at, updated_at
                ) VALUES (?, ?, 'manual', 'confirmed', 'single_choice', ?,
                          'invalid_json', '[]', '[]', '[]', '', '', ?, ?)
                """,
                (str(uuid.uuid4()), session_id, "无效题目", int(time.time()), int(time.time())),
            )

        # 测试发布接口（应该触发异常并回滚）
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/publish",
            headers=teacher_headers
        )
        assert response.status_code == 500
        data = response.json()
        assert data["code"] == "PUBLICATION_FAILED"

        # 验证没有创建课程内容
        with database.connect() as connection:
            contents = connection.execute(
                "SELECT * FROM course_contents WHERE class_id = ?", (class_id,)
            ).fetchall()
            assert len(contents) == 0

        # 验证发布状态已回滚
        with database.connect() as connection:
            row = connection.execute(
                "SELECT published_at FROM preparation_sessions WHERE id = ?",
                (session_id,)
            ).fetchone()
            assert row is not None
            assert row["published_at"] is None
