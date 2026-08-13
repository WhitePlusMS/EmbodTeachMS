from pathlib import Path

from fastapi.testclient import TestClient

from app.database import Database
from app.main import create_app


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


def test_get_course_overview_empty_class(tmp_path: Path) -> None:
    """获取空班级的课程概述，所有计数为0，文本为空字符串。"""
    app = create_app(
        database_path=tmp_path / "empty_overview.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_overview")

        # 创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "测试课程概述班",
                "joinPolicy": "free",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 获取课程概述
        response = client.get(
            f"/api/teaching-classes/{class_id}/course-overview",
            headers=teacher_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == "COURSE_OVERVIEW_FETCHED"

        data = body["data"]
        # 验证五项计数都为0
        assert data["knowledgePoints"] == 0
        assert data["knowledgeModules"] == 0
        assert data["teachingResources"] == 0
        assert data["questions"] == 0
        assert data["competencyObjectives"] == 0
        # 验证四项文本都为空字符串
        assert data["background"] == ""
        assert data["introduction"] == ""
        assert data["objectives"] == ""
        assert data["features"] == ""
        assert body["requestId"] == response.headers["X-Request-Id"]


def test_update_course_overview_text(tmp_path: Path) -> None:
    """更新课程概述文本并验证持久化。"""
    app = create_app(
        database_path=tmp_path / "update_overview.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_update")

        # 创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "更新测试班",
                "joinPolicy": "free",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 更新课程概述文本
        update_data = {
            "background": "这是课程背景",
            "introduction": "这是课程简介",
            "objectives": "这是课程目标",
            "features": "这是课程特色",
        }

        response = client.put(
            f"/api/teaching-classes/{class_id}/course-overview",
            headers=teacher_headers,
            json=update_data,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == "COURSE_OVERVIEW_UPDATED"

        data = body["data"]
        # 验证文本已更新
        assert data["background"] == "这是课程背景"
        assert data["introduction"] == "这是课程简介"
        assert data["objectives"] == "这是课程目标"
        assert data["features"] == "这是课程特色"
        # 计数仍为0
        assert data["knowledgePoints"] == 0
        assert data["knowledgeModules"] == 0
        assert data["teachingResources"] == 0
        assert data["questions"] == 0
        assert data["competencyObjectives"] == 0

        # 重新获取验证持久化
        response = client.get(
            f"/api/teaching-classes/{class_id}/course-overview",
            headers=teacher_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["background"] == "这是课程背景"
        assert data["introduction"] == "这是课程简介"
        assert data["objectives"] == "这是课程目标"
        assert data["features"] == "这是课程特色"


def test_course_overview_counts_published_content(tmp_path: Path) -> None:
    """课程概述只统计已发布的课程内容。"""
    database_path = tmp_path / "counts_overview.db"
    app = create_app(
        database_path=database_path,
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_counts")

        # 创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "计数测试班",
                "joinPolicy": "free",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 直接插入课程内容数据
        with Database(database_path).connect() as connection:
            # 插入已发布的内容
            connection.executemany(
                """
                INSERT INTO course_contents
                (id, class_id, content_type, publication_status, title, content, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    ("kp1", class_id, "knowledge_point", "published", "知识点1", "内容1", 1000, 1000),
                    ("kp2", class_id, "knowledge_point", "published", "知识点2", "内容2", 1001, 1001),
                    ("km1", class_id, "knowledge_module", "published", "模块1", "内容1", 1002, 1002),
                    ("tr1", class_id, "teaching_resource", "published", "资源1", "内容1", 1003, 1003),
                    ("q1", class_id, "question", "published", "问题1", "内容1", 1004, 1004),
                    ("co1", class_id, "competency_objective", "published", "目标1", "内容1", 1005, 1005),
                ],
            )
            # 插入草稿内容（不应计入统计）
            connection.executemany(
                """
                INSERT INTO course_contents
                (id, class_id, content_type, publication_status, title, content, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    ("kp-draft", class_id, "knowledge_point", "draft", "草稿知识点", "内容", 1006, 1006),
                    ("km-draft", class_id, "knowledge_module", "draft", "草稿模块", "内容", 1007, 1007),
                ],
            )

        # 获取课程概述
        response = client.get(
            f"/api/teaching-classes/{class_id}/course-overview",
            headers=teacher_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]

        # 验证只统计已发布内容
        assert data["knowledgePoints"] == 2  # 2个已发布知识点
        assert data["knowledgeModules"] == 1  # 1个已发布模块
        assert data["teachingResources"] == 1  # 1个已发布资源
        assert data["questions"] == 1  # 1个已发布问题
        assert data["competencyObjectives"] == 1  # 1个已发布目标


def test_course_overview_teacher_isolation(tmp_path: Path) -> None:
    """教师A不能访问教师B的课程概述。"""
    app = create_app(
        database_path=tmp_path / "isolation_overview.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_a_headers = register_user(client, "teacher_a")
        teacher_b_headers = register_user(client, "teacher_b")

        # 教师A创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_a_headers,
            json={
                "name": "教师A的班级",
                "joinPolicy": "free",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 教师B尝试获取教师A的课程概述
        response = client.get(
            f"/api/teaching-classes/{class_id}/course-overview",
            headers=teacher_b_headers,
        )
        assert response.status_code == 404
        assert response.json()["code"] == "RESOURCE_NOT_FOUND"

        # 教师B尝试更新教师A的课程概述
        response = client.put(
            f"/api/teaching-classes/{class_id}/course-overview",
            headers=teacher_b_headers,
            json={
                "background": "尝试修改",
                "introduction": "尝试修改",
                "objectives": "尝试修改",
                "features": "尝试修改",
            },
        )
        assert response.status_code == 404
        assert response.json()["code"] == "RESOURCE_NOT_FOUND"


def test_course_overview_learner_forbidden(tmp_path: Path) -> None:
    """学习者无权访问课程概述。"""
    app = create_app(
        database_path=tmp_path / "learner_forbidden_overview.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher")
        learner_headers = register_user(client, "learner", "learner")

        # 教师创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "测试班",
                "joinPolicy": "free",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 学习者尝试获取课程概述
        response = client.get(
            f"/api/teaching-classes/{class_id}/course-overview",
            headers=learner_headers,
        )
        assert response.status_code == 403
        assert response.json()["code"] == "AUTH_ROLE_FORBIDDEN"

        # 学习者尝试更新课程概述
        response = client.put(
            f"/api/teaching-classes/{class_id}/course-overview",
            headers=learner_headers,
            json={
                "background": "尝试修改",
                "introduction": "尝试修改",
                "objectives": "尝试修改",
                "features": "尝试修改",
            },
        )
        assert response.status_code == 403
        assert response.json()["code"] == "AUTH_ROLE_FORBIDDEN"


def test_course_overview_empty_strings_valid(tmp_path: Path) -> None:
    """空字符串是合法的课程概述文本值。"""
    app = create_app(
        database_path=tmp_path / "empty_strings_overview.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_empty")

        # 创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "空字符串测试班",
                "joinPolicy": "free",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 更新为空字符串
        update_data = {
            "background": "",
            "introduction": "",
            "objectives": "",
            "features": "",
        }

        response = client.put(
            f"/api/teaching-classes/{class_id}/course-overview",
            headers=teacher_headers,
            json=update_data,
        )
        assert response.status_code == 200

        # 验证可以正常保存和读取
        response = client.get(
            f"/api/teaching-classes/{class_id}/course-overview",
            headers=teacher_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["background"] == ""
        assert data["introduction"] == ""
        assert data["objectives"] == ""
        assert data["features"] == ""
