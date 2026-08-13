"""学习者课程内容详情 HTTP 端点测试"""

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
    return {
        "Authorization": f"Bearer {data['accessToken']}",
        "user_id": data["user"]["id"],
    }


def test_learner_can_access_published_content_detail(tmp_path: Path) -> None:
    """测试学习者可以访问已发布的课程内容详情"""
    app, database = build_app(
        database_path=tmp_path / "learner_content_detail.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        # 创建教师和学习者
        teacher_headers = register_user(client, "teacher_content_detail")
        learner_headers = register_user(client, "learner_content_detail", "learner")

        # 教师创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={"name": "测试教学班", "joinPolicy": "free"},
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 学习者加入教学班
        response = client.post(
            f"/api/teaching-classes/{class_id}/join",
            headers=learner_headers,
        )
        assert response.status_code == 201

        # 教师发布课程内容
        with database.connect() as connection:
            content_id = str(uuid.uuid4())
            connection.execute(
                """
                INSERT INTO course_contents (
                    id, class_id, content_type, publication_status,
                    title, content, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    content_id,
                    class_id,
                    "knowledge_module",
                    "published",
                    "测试知识模块",
                    "这是测试内容",
                    int(time.time()),
                    int(time.time()),
                ),
            )

            # 创建备课会话用于来源信息
            session_id = str(uuid.uuid4())
            connection.execute(
                """
                INSERT INTO preparation_sessions (
                    id, class_id, owner_teacher_id, upload_status,
                    parse_status, current_step, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    class_id,
                    teacher_headers["user_id"],
                    "uploaded",
                    "completed",
                    "publishing",
                    int(time.time()),
                    int(time.time()),
                ),
            )
            seed_preparation_state(
                connection,
                session_id,
                segments=[(1, "text", "课程内容段落")],
                highlights=[{
                    "id": "highlight-1",
                    "paragraphOrdinal": 1,
                    "startOffset": 0,
                    "endOffset": 4,
                    "createdAt": 1000,
                }],
                current_step="publishing",
            )

        # 学习者获取课程内容详情
        response = client.get(
            f"/api/teaching-classes/{class_id}/published-contents/{content_id}/learner",
            headers=learner_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "PUBLISHED_CONTENT_DETAIL_FETCHED"
        assert data["message"] == "课程内容详情获取成功"

        # 验证响应数据
        content_detail = data["data"]
        assert content_detail["id"] == content_id
        assert content_detail["classId"] == class_id
        assert content_detail["contentType"] == "knowledge_module"
        assert content_detail["publicationStatus"] == "published"
        assert content_detail["title"] == "测试知识模块"
        assert content_detail["content"] == "这是测试内容"
        assert content_detail["highlightsJson"] is not None
        assert content_detail["sourcePreparationSessionId"] == session_id
        assert content_detail["sourceTeacherId"] is not None


def test_learner_cannot_access_content_without_membership(tmp_path: Path) -> None:
    """测试非成员学习者不能访问课程内容详情"""
    app, database = build_app(
        database_path=tmp_path / "learner_no_access.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        # 创建教师和学习者
        teacher_headers = register_user(client, "teacher_no_access")
        learner_headers = register_user(client, "learner_no_access", "learner")

        # 教师创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={"name": "测试教学班", "joinPolicy": "free"},
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 教师发布课程内容
        with database.connect() as connection:
            content_id = str(uuid.uuid4())
            connection.execute(
                """
                INSERT INTO course_contents (
                    id, class_id, content_type, publication_status,
                    title, content, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    content_id,
                    class_id,
                    "knowledge_module",
                    "published",
                    "测试知识模块",
                    "这是测试内容",
                    int(time.time()),
                    int(time.time()),
                ),
            )

        # 学习者尝试访问课程内容详情（未加入班级）
        response = client.get(
            f"/api/teaching-classes/{class_id}/published-contents/{content_id}/learner",
            headers=learner_headers,
        )
        assert response.status_code == 403
        data = response.json()
        assert data["code"] == "CLASS_MEMBERSHIP_REQUIRED"
        assert data["message"] == "只有正式成员可以查看课程内容"


def test_learner_cannot_access_nonexistent_content(tmp_path: Path) -> None:
    """测试学习者不能访问不存在的课程内容"""
    app = create_app(
        database_path=tmp_path / "learner_nonexistent_content.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        # 创建教师和学习者
        teacher_headers = register_user(client, "teacher_nonexistent")
        learner_headers = register_user(client, "learner_nonexistent", "learner")

        # 教师创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={"name": "测试教学班", "joinPolicy": "free"},
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 学习者加入教学班
        response = client.post(
            f"/api/teaching-classes/{class_id}/join",
            headers=learner_headers,
        )
        assert response.status_code == 201

        # 学习者尝试访问不存在的课程内容
        nonexistent_content_id = str(uuid.uuid4())
        response = client.get(
            f"/api/teaching-classes/{class_id}/published-contents/{nonexistent_content_id}/learner",
            headers=learner_headers,
        )
        assert response.status_code == 404
        data = response.json()
        assert data["code"] == "RESOURCE_NOT_FOUND"
        assert data["message"] == "课程内容不存在或已删除"


def test_learner_cannot_access_draft_content(tmp_path: Path) -> None:
    """测试学习者不能访问草稿状态的课程内容"""
    app, database = build_app(
        database_path=tmp_path / "learner_draft_content.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        # 创建教师和学习者
        teacher_headers = register_user(client, "teacher_draft")
        learner_headers = register_user(client, "learner_draft", "learner")

        # 教师创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={"name": "测试教学班", "joinPolicy": "free"},
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 学习者加入教学班
        response = client.post(
            f"/api/teaching-classes/{class_id}/join",
            headers=learner_headers,
        )
        assert response.status_code == 201

        # 教师创建草稿内容
        with database.connect() as connection:
            content_id = str(uuid.uuid4())
            connection.execute(
                """
                INSERT INTO course_contents (
                    id, class_id, content_type, publication_status,
                    title, content, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    content_id,
                    class_id,
                    "knowledge_module",
                    "draft",  # 草稿状态
                    "草稿内容",
                    "这是草稿内容",
                    int(time.time()),
                    int(time.time()),
                ),
            )

        # 学习者尝试访问草稿内容
        response = client.get(
            f"/api/teaching-classes/{class_id}/published-contents/{content_id}/learner",
            headers=learner_headers,
        )
        assert response.status_code == 404
        data = response.json()
        assert data["code"] == "RESOURCE_NOT_FOUND"


def test_learner_cannot_access_other_class_content(tmp_path: Path) -> None:
    """测试学习者不能访问其他班级的课程内容"""
    app, database = build_app(
        database_path=tmp_path / "learner_other_class.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        # 创建两个教师和学习者
        teacher1_headers = register_user(client, "teacher1_other")
        teacher2_headers = register_user(client, "teacher2_other")
        learner_headers = register_user(client, "learner_other", "learner")

        # 教师1创建教学班并发布内容
        response = client.post(
            "/api/teaching-classes",
            headers=teacher1_headers,
            json={"name": "教学班1", "joinPolicy": "free"},
        )
        assert response.status_code == 201
        class1_id = response.json()["data"]["id"]

        with database.connect() as connection:
            content1_id = str(uuid.uuid4())
            connection.execute(
                """
                INSERT INTO course_contents (
                    id, class_id, content_type, publication_status,
                    title, content, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    content1_id,
                    class1_id,
                    "knowledge_module",
                    "published",
                    "教学班1内容",
                    "这是教学班1的内容",
                    int(time.time()),
                    int(time.time()),
                ),
            )

        # 教师2创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher2_headers,
            json={"name": "教学班2", "joinPolicy": "free"},
        )
        assert response.status_code == 201
        class2_id = response.json()["data"]["id"]

        # 学习者加入教学班2
        response = client.post(
            f"/api/teaching-classes/{class2_id}/join",
            headers=learner_headers,
        )
        assert response.status_code == 201

        # 学习者尝试访问教学班1的内容
        response = client.get(
            f"/api/teaching-classes/{class1_id}/published-contents/{content1_id}/learner",
            headers=learner_headers,
        )
        assert response.status_code == 403
        data = response.json()
        assert data["code"] == "CLASS_MEMBERSHIP_REQUIRED"


def test_content_detail_includes_homework_fields(tmp_path: Path) -> None:
    """测试作业内容详情包含作业特有字段"""
    app, database = build_app(
        database_path=tmp_path / "content_detail_homework.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        # 创建教师和学习者
        teacher_headers = register_user(client, "teacher_homework")
        learner_headers = register_user(client, "learner_homework", "learner")

        # 教师创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={"name": "测试教学班", "joinPolicy": "free"},
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 学习者加入教学班
        response = client.post(
            f"/api/teaching-classes/{class_id}/join",
            headers=learner_headers,
        )
        assert response.status_code == 201

        # 教师发布作业内容
        with database.connect() as connection:
            content_id = str(uuid.uuid4())
            due_at = int(time.time()) + 86400  # 24小时后
            connection.execute(
                """
                INSERT INTO course_contents (
                    id, class_id, content_type, publication_status,
                    title, content, due_at, description, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    content_id,
                    class_id,
                    "homework",
                    "published",
                    "数学作业",
                    "完成练习题1-10",
                    due_at,
                    "请认真完成作业",
                    int(time.time()),
                    int(time.time()),
                ),
            )

        # 学习者获取作业内容详情
        response = client.get(
            f"/api/teaching-classes/{class_id}/published-contents/{content_id}/learner",
            headers=learner_headers,
        )
        assert response.status_code == 200
        data = response.json()

        # 验证作业特有字段
        content_detail = data["data"]
        assert content_detail["contentType"] == "homework"
        assert content_detail["dueAt"] == due_at
        assert content_detail["description"] == "请认真完成作业"
