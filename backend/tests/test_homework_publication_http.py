"""作业发布 HTTP 端点测试"""

import json
import time
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

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


def test_homework_publication_success(tmp_path: Path) -> None:
    """测试作业发布成功场景"""
    app, database = build_app(
        database_path=tmp_path / "homework_publication_success.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_homework_success")
        learner_headers = register_user(client, "learner_homework_success", "learner")

        # 创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={"name": "测试教学班", "joinPolicy": "free"},
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]
        assert client.post(
            f"/api/teaching-classes/{class_id}/join",
            headers=learner_headers,
        ).status_code == 201

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

        # 测试作业发布接口
        homework_request = {
            "title": "数学作业",
            "dueAt": int(time.time()) + 86400,  # 24小时后
            "description": "完成以下练习题"
        }

        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/publish-homework",
            headers=teacher_headers,
            json=homework_request
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "HOMEWORK_PUBLISHED"
        assert data["message"] == "作业发布成功"

        # 验证响应数据
        response_data = data["data"]
        assert "session" in response_data
        assert "homeworkId" in response_data
        assert response_data["homeworkId"] != ""

        # 验证发布状态
        session_data = response_data["session"]
        publication_draft = json.loads(session_data["publicationDraftJson"])
        assert publication_draft["published_at"] is not None
        assert len(publication_draft["course_content_ids"]) > 0

        # 验证课程内容已创建
        with database.connect() as connection:
            contents = connection.execute(
                "SELECT * FROM course_contents WHERE class_id = ?", (class_id,)
            ).fetchall()
        assert len(contents) == len(publication_draft["course_content_ids"])

        # 验证作业内容
        with database.connect() as connection:
            homework = connection.execute(
                "SELECT * FROM course_contents WHERE content_type = 'homework'",
            ).fetchone()
            homework_question = connection.execute(
                """
                SELECT
                    cc.content, cq.question_type, cq.stem,
                    cq.options_json, cq.correct_answers_json
                FROM homework_questions hq
                JOIN course_contents cc ON cc.id = hq.question_id
                JOIN course_content_questions cq ON cq.content_id = cc.id
                WHERE hq.homework_id = ?
                """,
                (response_data["homeworkId"],),
            ).fetchone()
            homework_question_id = connection.execute(
                "SELECT question_id FROM homework_questions WHERE homework_id = ?",
                (response_data["homeworkId"],),
            ).fetchone()["question_id"]
        assert homework is not None
        assert homework["title"] == "数学作业"
        assert homework["due_at"] == homework_request["dueAt"]
        assert homework["description"] == "完成以下练习题"
        assert homework_question is not None
        assert homework_question["content"] == "测试题目"
        assert "正确答案" not in homework_question["content"]
        assert homework_question["question_type"] == "single_choice"
        assert json.loads(homework_question["options_json"]) == ["选项1", "选项2"]
        assert json.loads(homework_question["correct_answers_json"]) == [0]

        learner_detail = client.get(
            f"/api/teaching-classes/{class_id}/published-contents/{homework_question_id}/learner",
            headers=learner_headers,
        )
        assert learner_detail.status_code == 200
        learner_question = learner_detail.json()["data"]["question"]
        assert learner_question["stem"] == "测试题目"
        assert learner_question["options"] == ["选项1", "选项2"]
        assert "answers" not in learner_question
        assert "explanation" not in learner_question
        assert "正确答案" not in learner_detail.text
        assert "解析" not in learner_detail.text

        # 教师预览应返回作业截止时间和描述
        response = client.get(
            f"/api/teaching-classes/{class_id}/published-contents",
            headers=teacher_headers,
        )
        assert response.status_code == 200
        published_items = response.json()["data"]["items"]
        published_homework = next(
            item for item in published_items if item["contentType"] == "homework"
        )
        assert published_homework["dueAt"] == homework_request["dueAt"]
        assert published_homework["description"] == "完成以下练习题"


def test_homework_publication_field_validation(tmp_path: Path) -> None:
    """测试作业字段验证失败"""
    app, database = build_app(
        database_path=tmp_path / "homework_field_validation.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_homework_validation")

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

        # 模拟解析完成状态
        with database.connect() as connection:
            session_id = connection.execute(
                "SELECT id FROM preparation_sessions WHERE class_id = ?", (class_id,)
            ).fetchone()["id"]

            connection.execute(
                "UPDATE preparation_sessions SET parse_status = 'completed' WHERE id = ?",
                (session_id,)
            )

        # 测试空标题
        homework_request = {
            "title": "",
            "dueAt": int(time.time()) + 86400,
            "description": "作业描述"
        }

        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/publish-homework",
            headers=teacher_headers,
            json=homework_request
        )
        assert response.status_code == 422
        data = response.json()
        assert data["code"] == "REQUEST_VALIDATION_ERROR"

        # 测试截止时间小于当前时间
        homework_request = {
            "title": "数学作业",
            "dueAt": int(time.time()) - 86400,  # 24小时前
            "description": "作业描述"
        }

        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/publish-homework",
            headers=teacher_headers,
            json=homework_request
        )
        assert response.status_code == 400
        data = response.json()
        assert data["code"] == "HOMEWORK_DUE_AT_INVALID"


def test_homework_publication_no_confirmed_questions(tmp_path: Path) -> None:
    """测试发布作业时没有确认题失败"""
    app, database = build_app(
        database_path=tmp_path / "homework_no_questions.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_homework_no_questions")

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

        # 模拟解析完成状态但没有确认题
        with database.connect() as connection:
            session_id = connection.execute(
                "SELECT id FROM preparation_sessions WHERE class_id = ?", (class_id,)
            ).fetchone()["id"]

            # 设置候选题（未确认）
            questions = [{
                "id": str(uuid.uuid4()),
                "source": "manual",
                "review_status": "candidate",
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
                questions=questions,
                current_step="publishing",
            )

        # 测试作业发布接口
        homework_request = {
            "title": "数学作业",
            "dueAt": int(time.time()) + 86400,
            "description": "完成以下练习题"
        }

        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/publish-homework",
            headers=teacher_headers,
            json=homework_request
        )
        assert response.status_code == 400
        data = response.json()
        assert data["code"] == "HOMEWORK_PUBLICATION_NO_CONFIRMED_QUESTIONS"


def test_homework_publication_already_published(tmp_path: Path) -> None:
    """测试重复发布作业失败"""
    app, database = build_app(
        database_path=tmp_path / "homework_already_published.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_homework_already")

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

        # 模拟已发布状态
        with database.connect() as connection:
            session_id = connection.execute(
                "SELECT id FROM preparation_sessions WHERE class_id = ?", (class_id,)
            ).fetchone()["id"]

            connection.execute(
                """
                UPDATE preparation_sessions
                SET parse_status = 'completed', current_step = 'publishing',
                    published_at = ?
                WHERE id = ?
                """,
                (int(time.time()), session_id)
            )

        # 测试作业发布接口
        homework_request = {
            "title": "数学作业",
            "dueAt": int(time.time()) + 86400,
            "description": "完成以下练习题"
        }

        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/publish-homework",
            headers=teacher_headers,
            json=homework_request
        )
        assert response.status_code == 409
        data = response.json()
        assert data["code"] == "PUBLICATION_ALREADY_EXISTS"


def test_homework_publication_cross_class_access(tmp_path: Path) -> None:
    """测试跨班访问权限验证"""
    app, database = build_app(
        database_path=tmp_path / "homework_cross_class.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        # 创建两个教师
        teacher1_headers = register_user(client, "teacher1_homework")
        teacher2_headers = register_user(client, "teacher2_homework")

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

        # 模拟解析完成状态
        with database.connect() as connection:
            session_id = connection.execute(
                "SELECT id FROM preparation_sessions WHERE class_id = ?", (class_id,)
            ).fetchone()["id"]

            connection.execute(
                "UPDATE preparation_sessions SET parse_status = 'completed' WHERE id = ?",
                (session_id,)
            )

        # 教师2尝试发布教师1的会话
        homework_request = {
            "title": "数学作业",
            "dueAt": int(time.time()) + 86400,
            "description": "完成以下练习题"
        }

        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/publish-homework",
            headers=teacher2_headers,
            json=homework_request
        )
        assert response.status_code == 404
        data = response.json()
        assert data["code"] == "RESOURCE_NOT_FOUND"


def test_homework_publication_transaction_rollback(tmp_path: Path) -> None:
    """测试作业发布事务回滚"""
    app, database = build_app(
        database_path=tmp_path / "homework_rollback.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_homework_rollback")

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

        # 模拟解析完成状态，但设置无效的题目数据（会触发异常）
        with database.connect() as connection:
            session_id = connection.execute(
                "SELECT id FROM preparation_sessions WHERE class_id = ?", (class_id,)
            ).fetchone()["id"]

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

        # 测试作业发布接口（应该触发异常并回滚）
        homework_request = {
            "title": "数学作业",
            "dueAt": int(time.time()) + 86400,
            "description": "完成以下练习题"
        }

        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/publish-homework",
            headers=teacher_headers,
            json=homework_request
        )
        assert response.status_code == 500
        data = response.json()
        assert data["code"] == "HOMEWORK_PUBLICATION_FAILED"

        # 验证没有创建课程内容
        with database.connect() as connection:
            contents = connection.execute(
                "SELECT * FROM course_contents WHERE class_id = ?", (class_id,)
            ).fetchall()
            assert len(contents) == 0

        # 验证发布状态已回滚
        with database.connect() as connection:
            row = connection.execute(
                "SELECT published_at FROM preparation_sessions WHERE class_id = ?",
                (class_id,)
            ).fetchone()
            assert row is not None
            assert row["published_at"] is None
