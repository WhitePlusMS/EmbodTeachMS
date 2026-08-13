import json
import time
from pathlib import Path

from fastapi.testclient import TestClient

from app.teaching_classes.course_content_publisher import CourseContentPublisher
from tests.conftest import build_app, seed_preparation_state


def teacher_headers(client):
    """创建教师并返回认证头信息"""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "test_teacher",
            "password": "StrongPass123!",
            "displayName": "测试教师",
            "role": "teacher",
        },
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['data']['accessToken']}"}


def test_publish_knowledge_modules(tmp_path: Path):
    """测试发布知识模块功能"""
    app, database = build_app(
        database_path=tmp_path / "test.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        headers = teacher_headers(client)

        # 创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=headers,
            json={"name": "测试教学班", "joinPolicy": "free"},
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 创建备课会话
        response = client.post(f"/api/teaching-classes/{class_id}/preparation-session", headers=headers)
        assert response.status_code == 201
        session_id = response.json()["data"]["id"]

        # 模拟解析完成状态和段落数据
        with database.connect() as connection:
            seed_preparation_state(
                connection,
                session_id,
                segments=[
                    (1, "paragraph", "这是第一个测试段落内容"),
                    (2, "paragraph", "这是第二个测试段落内容"),
                ],
                highlights=[
                    {
                        "id": "highlight_1",
                        "paragraphOrdinal": 1,
                        "startOffset": 0,
                        "endOffset": 4,
                        "createdAt": int(time.time()),
                    }
                ],
            )

            # 获取会话记录
            session_row = connection.execute(
                "SELECT * FROM preparation_sessions WHERE id = ?", (session_id,)
            ).fetchone()

            # 测试发布器
            publisher = CourseContentPublisher(lambda: int(time.time()))
            content_ids = publisher.publish_course_content(connection, session_row, class_id)

            # 验证发布结果
            assert len(content_ids) > 0

            # 检查是否创建了知识模块
            content_rows = connection.execute(
                "SELECT * FROM course_contents WHERE class_id = ?", (class_id,)
            ).fetchall()

            assert len(content_rows) == 1  # 应该创建1个知识模块
            assert content_rows[0]["content_type"] == "knowledge_module"
            assert content_rows[0]["publication_status"] == "published"
            assert "段落 1" in content_rows[0]["title"]
            assert "这是第一个测试段落内容" in content_rows[0]["content"]


def test_publish_questions(tmp_path: Path):
    """测试发布课堂练习功能"""
    app, database = build_app(
        database_path=tmp_path / "test.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        headers = teacher_headers(client)

        # 创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=headers,
            json={"name": "测试教学班", "joinPolicy": "free"},
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 创建备课会话
        response = client.post(f"/api/teaching-classes/{class_id}/preparation-session", headers=headers)
        assert response.status_code == 201
        session_id = response.json()["data"]["id"]

        # 模拟解析完成状态和题目数据
        with database.connect() as connection:
            # 设置会话状态和已确认题目
            seed_preparation_state(
                connection,
                session_id,
                questions=[
                            {
                                "id": "question_1",
                                "source": "manual",
                                "review_status": "confirmed",
                                "type": "single_choice",
                                "stem": "这是一个测试题目",
                                "options": ["选项A", "选项B", "选项C"],
                                "answers": [0],
                                "knowledge_points": ["知识点1"],
                                "highlight_source_ids": [],
                                "hint": "这是提示",
                                "explanation": "这是解析",
                                "created_at": int(time.time()),
                                "updated_at": int(time.time()),
                            },
                            {
                                "id": "question_2",
                                "source": "candidate",
                                "review_status": "candidate",  # 未确认的题目
                                "type": "multiple_choice",
                                "stem": "这是未确认题目",
                                "options": ["选项A", "选项B"],
                                "answers": [0, 1],
                                "knowledge_points": ["知识点2"],
                                "highlight_source_ids": [],
                                "hint": "",
                                "explanation": "",
                                "created_at": int(time.time()),
                                "updated_at": int(time.time()),
                            },
                        ],
            )

            # 获取会话记录
            session_row = connection.execute(
                "SELECT * FROM preparation_sessions WHERE id = ?", (session_id,)
            ).fetchone()

            # 测试发布器
            publisher = CourseContentPublisher(lambda: int(time.time()))
            content_ids = publisher.publish_course_content(connection, session_row, class_id)

            # 验证发布结果
            assert len(content_ids) > 0

            # 检查是否创建了课堂练习
            content_rows = connection.execute(
                "SELECT * FROM course_contents WHERE class_id = ?", (class_id,)
            ).fetchall()

            assert len(content_rows) == 1  # 应该只创建1个已确认的题目
            assert content_rows[0]["content_type"] == "question"
            assert content_rows[0]["publication_status"] == "published"
            assert "课堂练习" in content_rows[0]["title"]
            assert "这是一个测试题目" in content_rows[0]["content"]
def test_publish_empty_content(tmp_path: Path):
    """测试发布空内容的情况"""
    app, database = build_app(
        database_path=tmp_path / "test.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        headers = teacher_headers(client)

        # 创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=headers,
            json={"name": "测试教学班", "joinPolicy": "free"},
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 创建备课会话
        response = client.post(f"/api/teaching-classes/{class_id}/preparation-session", headers=headers)
        assert response.status_code == 201
        session_id = response.json()["data"]["id"]

        # 模拟空内容状态
        with database.connect() as connection:
            seed_preparation_state(connection, session_id)

            # 获取会话记录
            session_row = connection.execute(
                "SELECT * FROM preparation_sessions WHERE id = ?", (session_id,)
            ).fetchone()

            # 测试发布器
            publisher = CourseContentPublisher(lambda: int(time.time()))
            content_ids = publisher.publish_course_content(connection, session_row, class_id)

            # 验证没有创建任何内容
            assert len(content_ids) == 0

            # 检查数据库
            content_rows = connection.execute(
                "SELECT * FROM course_contents WHERE class_id = ?", (class_id,)
            ).fetchall()
            assert len(content_rows) == 0
