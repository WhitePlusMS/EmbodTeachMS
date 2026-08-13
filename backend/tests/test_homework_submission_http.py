"""作业提交 HTTP 端点测试"""

import json
import time
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from tests.conftest import build_app
from tests.question_factory import insert_published_question


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


def link_homework_question(connection, homework_id: str, question_id: str) -> None:
    """测试数据显式建立作业与题目的领域关系。"""
    connection.execute(
        """
        INSERT INTO homework_questions (homework_id, question_id, ordinal)
        VALUES (?, ?, 0)
        """,
        (homework_id, question_id),
    )


def test_save_homework_draft_success(tmp_path: Path) -> None:
    """测试保存作业草稿成功场景"""
    app, database = build_app(
        database_path=tmp_path / "homework_draft_success.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_homework_draft")
        learner_headers = register_user(client, "learner_homework_draft", "learner")

        # 创建教学班
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

        # 创建作业
        with database.connect() as connection:
            homework_id = str(uuid.uuid4())
            now = int(time.time())
            connection.execute(
                """
                INSERT INTO course_contents
                (id, class_id, content_type, publication_status, title, content, due_at, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (homework_id, class_id, "homework", "published", "数学作业", "作业内容", now + 86400, "作业描述", now, now),
            )

            # 创建作业题目
            question_id = insert_published_question(
                connection,
                class_id,
                stem="测试题目",
                options=["A", "B"],
                correct_answers=[0],
                title="题目1",
                now=now,
            )
            link_homework_question(connection, homework_id, question_id)

        # 测试保存草稿
        draft_request = {
            "classId": class_id,
            "homeworkId": homework_id,
            "answers": {question_id: [0]}
        }

        response = client.post(
            f"/api/teaching-classes/{class_id}/homework/{homework_id}/save-draft",
            headers=learner_headers,
            json=draft_request
        )
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "HOMEWORK_DRAFT_SAVED"
        assert data["message"] == "作业草稿保存成功"

        # 验证响应数据
        submission_data = data["data"]
        assert submission_data["status"] == "draft"
        assert submission_data["homeworkId"] == homework_id
        assert submission_data["learnerId"] is not None
        assert submission_data["draftSavedAt"] is not None

        # 验证数据库记录
        with database.connect() as connection:
            submission_row = connection.execute(
                "SELECT * FROM homework_submissions WHERE homework_id = ? AND learner_id = ?",
                (homework_id, submission_data["learnerId"])
            ).fetchone()
            assert submission_row is not None
            assert submission_row["status"] == "draft"
            assert json.loads(submission_row["answers_json"]) == {question_id: [0]}


def test_submit_homework_success(tmp_path: Path) -> None:
    """测试提交作业成功场景"""
    app, database = build_app(
        database_path=tmp_path / "homework_submit_success.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_homework_submit")
        learner_headers = register_user(client, "learner_homework_submit", "learner")

        # 创建教学班
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

        # 创建作业
        with database.connect() as connection:
            homework_id = str(uuid.uuid4())
            now = int(time.time())
            connection.execute(
                """
                INSERT INTO course_contents
                (id, class_id, content_type, publication_status, title, content, due_at, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (homework_id, class_id, "homework", "published", "数学作业", "作业内容", now + 86400, "作业描述", now, now),
            )

            # 创建作业题目
            question_id = insert_published_question(
                connection,
                class_id,
                stem="测试题目",
                options=["A", "B"],
                correct_answers=[0],
                title="题目1",
                now=now,
            )
            link_homework_question(connection, homework_id, question_id)

        manual_complete = client.post(
            f"/api/teaching-classes/{class_id}/contents/{homework_id}/complete",
            headers=learner_headers,
        )
        assert manual_complete.status_code == 400
        assert manual_complete.json()["code"] == "HOMEWORK_COMPLETION_REQUIRES_SUBMISSION"

        # 测试提交作业
        submit_request = {
            "classId": class_id,
            "homeworkId": homework_id,
            "answers": {question_id: [0]}
        }

        response = client.post(
            f"/api/teaching-classes/{class_id}/homework/{homework_id}/submit",
            headers=learner_headers,
            json=submit_request
        )
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "HOMEWORK_SUBMITTED"
        assert data["message"] == "作业提交成功"

        # 验证响应数据
        result_data = data["data"]
        assert result_data["submission"]["status"] == "submitted"
        assert result_data["submission"]["homeworkId"] == homework_id
        assert result_data["submission"]["submittedAt"] is not None
        assert result_data["submission"]["totalScore"] == 1  # 应该得1分
        assert result_data["submission"]["correctCount"] == 1  # 应该正确1题

        # 验证判分详情
        assert len(result_data["questions"]) == 1
        question_result = result_data["questions"][0]
        assert question_result["isCorrect"] == True
        assert question_result["score"] == 1

        detail = client.get(
            f"/api/teaching-classes/{class_id}/published-contents/{homework_id}/learner",
            headers=learner_headers,
        )
        assert detail.status_code == 200
        assert detail.json()["data"]["completed"] is True

        with database.connect() as connection:
            completion = connection.execute(
                "SELECT id FROM course_content_completions WHERE learner_id = ? AND class_id = ? AND content_id = ?",
                (data["data"]["submission"]["learnerId"], class_id, homework_id),
            ).fetchone()
        assert completion is not None


def test_submit_homework_late_submission(tmp_path: Path) -> None:
    """测试迟交作业场景"""
    app, database = build_app(
        database_path=tmp_path / "homework_late_submission.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_homework_late")
        learner_headers = register_user(client, "learner_homework_late", "learner")

        # 创建教学班
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

        # 创建已过期的作业
        with database.connect() as connection:
            homework_id = str(uuid.uuid4())
            now = int(time.time())
            connection.execute(
                """
                INSERT INTO course_contents
                (id, class_id, content_type, publication_status, title, content, due_at, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (homework_id, class_id, "homework", "published", "过期作业", "作业内容", now - 86400, "已过期作业", now, now),
            )

            # 创建作业题目
            question_id = insert_published_question(
                connection,
                class_id,
                stem="测试题目",
                options=["A", "B"],
                correct_answers=[0],
                title="题目1",
                now=now,
            )
            link_homework_question(connection, homework_id, question_id)

        # 测试提交过期作业
        submit_request = {
            "classId": class_id,
            "homeworkId": homework_id,
            "answers": {question_id: [0]}
        }

        response = client.post(
            f"/api/teaching-classes/{class_id}/homework/{homework_id}/submit",
            headers=learner_headers,
            json=submit_request
        )
        assert response.status_code == 201
        data = response.json()

        # 验证迟交标记
        result_data = data["data"]
        assert result_data["submission"]["isLateSubmission"] == True
        assert result_data["submission"]["status"] == "submitted"


def test_homework_submission_detail(tmp_path: Path) -> None:
    """测试获取作业提交详情"""
    app, database = build_app(
        database_path=tmp_path / "homework_detail.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_homework_detail")
        learner_headers = register_user(client, "learner_homework_detail", "learner")

        # 创建教学班
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

        # 创建作业
        with database.connect() as connection:
            homework_id = str(uuid.uuid4())
            now = int(time.time())
            connection.execute(
                """
                INSERT INTO course_contents
                (id, class_id, content_type, publication_status, title, content, due_at, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (homework_id, class_id, "homework", "published", "数学作业", "作业内容", now + 86400, "作业描述", now, now),
            )

        # 测试获取提交详情（无提交记录）
        response = client.get(
            f"/api/teaching-classes/{class_id}/homework/{homework_id}/submission",
            headers=learner_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "HOMEWORK_SUBMISSION_DETAIL_FETCHED"
        assert data["data"]["submission"] is None
        assert data["data"]["homework"]["id"] == homework_id


def test_homework_submission_detail_rejects_cross_class_homework_id(tmp_path: Path) -> None:
    """成员不能借助本班路径读取另一教学班的作业内容。"""
    app, database = build_app(
        database_path=tmp_path / "homework_detail_cross_class.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_homework_detail_cross_class")
        learner_headers = register_user(client, "learner_homework_detail_cross_class", "learner")
        first_class_id = client.post(
            "/api/teaching-classes", headers=teacher_headers,
            json={"name": "学习者所在班", "joinPolicy": "free"},
        ).json()["data"]["id"]
        second_class_id = client.post(
            "/api/teaching-classes", headers=teacher_headers,
            json={"name": "未加入班级", "joinPolicy": "free"},
        ).json()["data"]["id"]
        assert client.post(
            f"/api/teaching-classes/{first_class_id}/join", headers=learner_headers,
        ).status_code == 201

        homework_id = str(uuid.uuid4())
        now = int(time.time())
        with database.connect() as connection:
            connection.execute(
                """
                INSERT INTO course_contents
                (id, class_id, content_type, publication_status, title, content, due_at, description, created_at, updated_at)
                VALUES (?, ?, 'homework', 'published', ?, ?, ?, ?, ?, ?)
                """,
                (homework_id, second_class_id, "另一班作业", "保密正文", now + 86400, "保密描述", now, now),
            )

        response = client.get(
            f"/api/teaching-classes/{first_class_id}/homework/{homework_id}/submission",
            headers=learner_headers,
        )
        assert response.status_code == 404
        assert response.json()["code"] == "HOMEWORK_NOT_FOUND"


def test_homework_list_for_learner(tmp_path: Path) -> None:
    """测试学习者获取作业列表"""
    app, database = build_app(
        database_path=tmp_path / "homework_list.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_homework_list")
        learner_headers = register_user(client, "learner_homework_list", "learner")

        # 创建教学班
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

        # 创建作业
        with database.connect() as connection:
            homework_id = str(uuid.uuid4())
            now = int(time.time())
            connection.execute(
                """
                INSERT INTO course_contents
                (id, class_id, content_type, publication_status, title, content, due_at, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (homework_id, class_id, "homework", "published", "数学作业", "作业内容", now + 86400, "作业描述", now, now),
            )

        # 测试获取作业列表
        response = client.get(
            f"/api/teaching-classes/{class_id}/homework",
            headers=learner_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "HOMEWORK_LIST_FETCHED"
        assert len(data["data"]["items"]) == 1
        assert data["data"]["items"][0]["id"] == homework_id
        assert data["data"]["submissions"] == {}


def test_homework_submission_validation_errors(tmp_path: Path) -> None:
    """测试作业提交验证错误"""
    app, database = build_app(
        database_path=tmp_path / "homework_validation.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_homework_validation")
        learner_headers = register_user(client, "learner_homework_validation", "learner")

        # 创建教学班
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

        # 创建作业
        with database.connect() as connection:
            homework_id = str(uuid.uuid4())
            now = int(time.time())
            connection.execute(
                """
                INSERT INTO course_contents
                (id, class_id, content_type, publication_status, title, content, due_at, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (homework_id, class_id, "homework", "published", "数学作业", "作业内容", now + 86400, "作业描述", now, now),
            )

        # 测试无效的题目ID
        submit_request = {
            "classId": class_id,
            "homeworkId": homework_id,
            "answers": {"invalid_question_id": [0]}
        }

        response = client.post(
            f"/api/teaching-classes/{class_id}/homework/{homework_id}/submit",
            headers=learner_headers,
            json=submit_request
        )
        assert response.status_code == 400
        data = response.json()
        assert data["code"] == "INVALID_QUESTION_ID"

        # 测试重复提交
        with database.connect() as connection:
            question_id = insert_published_question(
                connection,
                class_id,
                stem="测试题目",
                options=["A", "B"],
                correct_answers=[0],
                title="题目1",
                now=now,
            )
            link_homework_question(connection, homework_id, question_id)

        # 先成功提交一次
        submit_request = {
            "classId": class_id,
            "homeworkId": homework_id,
            "answers": {question_id: [0]}
        }
        response = client.post(
            f"/api/teaching-classes/{class_id}/homework/{homework_id}/submit",
            headers=learner_headers,
            json=submit_request
        )
        assert response.status_code == 201

        # 再次提交
        response = client.post(
            f"/api/teaching-classes/{class_id}/homework/{homework_id}/submit",
            headers=learner_headers,
            json=submit_request
        )
        assert response.status_code == 400
        data = response.json()
        assert data["code"] == "HOMEWORK_ALREADY_SUBMITTED"
