"""教师作业管理与确定性统计 HTTP 测试。"""

import json
import time
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from tests.conftest import build_app
from tests.question_factory import insert_published_question


def register(client: TestClient, username: str, role: str) -> tuple[dict[str, str], str]:
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
    return {"Authorization": f"Bearer {data['accessToken']}"}, data["user"]["id"]


def create_class(client: TestClient, headers: dict[str, str], name: str) -> str:
    response = client.post(
        "/api/teaching-classes",
        headers=headers,
        json={"name": name, "joinPolicy": "free"},
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def join(client: TestClient, class_id: str, headers: dict[str, str]) -> None:
    response = client.post(f"/api/teaching-classes/{class_id}/join", headers=headers)
    assert response.status_code == 201


def seed_homework(database, class_id: str, *, due_at: int) -> tuple[str, str, str]:
    homework_id, question_one_id, question_two_id = [str(uuid.uuid4()) for _ in range(3)]
    now = int(time.time())
    with database.connect() as connection:
        connection.execute(
            """
            INSERT INTO course_contents
              (id, class_id, content_type, publication_status, title, content,
               due_at, description, created_at, updated_at)
            VALUES (?, ?, 'homework', 'published', ?, ?, ?, ?, ?, ?)
            """,
            (homework_id, class_id, "机器人作业", "完成两道题", due_at, "作业说明", now, now),
        )
        insert_published_question(
            connection,
            class_id,
            content_id=question_one_id,
            stem="机器人需要什么？",
            options=["传感器", "盲目运行"],
            correct_answers=[0],
            knowledge_points=["传感器"],
            title="题目一",
            now=now,
        )
        insert_published_question(
            connection,
            class_id,
            content_id=question_two_id,
            stem="控制系统依据什么修正？",
            options=["反馈", "猜测"],
            correct_answers=[0],
            knowledge_points=["反馈控制"],
            title="题目二",
            now=now,
        )
        connection.executemany(
            "INSERT INTO homework_questions (homework_id, question_id, ordinal) VALUES (?, ?, ?)",
            [(homework_id, question_one_id, 0), (homework_id, question_two_id, 1)],
        )
    return homework_id, question_one_id, question_two_id


def test_teacher_homework_stats_are_scoped_and_deterministic(tmp_path: Path) -> None:
    app, database = build_app(
        database_path=tmp_path / "teacher-homework-management.db",
        jwt_secret="test-secret-with-enough-length",
    )
    with TestClient(app) as client:
        teacher, _ = register(client, "homework_stats_teacher", "teacher")
        other_teacher, _ = register(client, "homework_stats_other_teacher", "teacher")
        learner_one, learner_one_id = register(client, "homework_stats_learner_one", "learner")
        learner_two, learner_two_id = register(client, "homework_stats_learner_two", "learner")
        pending_learner, pending_learner_id = register(client, "homework_stats_pending", "learner")
        outsider, _ = register(client, "homework_stats_outsider", "learner")
        class_id = create_class(client, teacher, "作业统计班")
        other_class_id = create_class(client, other_teacher, "其他作业统计班")
        join(client, class_id, learner_one)
        join(client, class_id, learner_two)
        join(client, class_id, pending_learner)
        homework_id, question_one_id, question_two_id = seed_homework(
            database, class_id, due_at=int(time.time()) + 3600
        )

        first_submit = client.post(
            f"/api/teaching-classes/{class_id}/homework/{homework_id}/submit",
            headers=learner_one,
            json={
                "classId": class_id,
                "homeworkId": homework_id,
                "answers": {question_one_id: [0], question_two_id: [1]},
            },
        )
        assert first_submit.status_code == 201
        second_submit = client.post(
            f"/api/teaching-classes/{class_id}/homework/{homework_id}/submit",
            headers=learner_two,
            json={
                "classId": class_id,
                "homeworkId": homework_id,
                "answers": {question_one_id: [1], question_two_id: [0]},
            },
        )
        assert second_submit.status_code == 201

        # 将一个真实已提交记录标记为迟交，仍只改变判分事实的迟交字段。
        with database.connect() as connection:
            connection.execute(
                "UPDATE homework_submissions SET is_late_submission = 1 WHERE learner_id = ? AND homework_id = ?",
                (learner_two_id, homework_id),
            )
            now = int(time.time())
            connection.execute(
                """
                INSERT INTO homework_submissions
                  (id, learner_id, class_id, homework_id, status, answers_json, grading_json,
                   submitted_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'submitted', ?, '{}', ?, ?, ?)
                """,
                (str(uuid.uuid4()), pending_learner_id, class_id, homework_id, json.dumps({}), now, now, now),
            )

        response = client.get(
            f"/api/teaching-classes/{class_id}/teacher-homework", headers=teacher
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["noData"] is False
        assert len(data["items"]) == 1
        item = data["items"][0]
        assert item["status"] == "published"
        assert item["totalLearners"] == 3
        assert item["submittedCount"] == 3
        assert set(item["submittedLearnerIds"]) == {
            learner_one_id,
            learner_two_id,
            pending_learner_id,
        }
        assert item["lateCount"] == 1
        assert item["correctRate"] == 50.0
        assert item["pendingReviewCount"] == 1
        assert item["dataStatus"] == "insufficient_data"
        assert len(item["questionStats"]) == 2
        assert item["questionStats"][0]["correctRate"] == 50.0
        assert item["questionStats"][0]["commonErrorReason"] == "选项2（1次）"
        assert item["questionStats"][1]["commonErrorReason"] == "选项2（1次）"

        refreshed = client.get(
            f"/api/teaching-classes/{class_id}/teacher-homework", headers=teacher
        ).json()
        assert refreshed["code"] == response.json()["code"]
        assert refreshed["message"] == response.json()["message"]
        assert refreshed["data"] == response.json()["data"]
        assert client.get(
            f"/api/teaching-classes/{other_class_id}/teacher-homework", headers=teacher
        ).status_code == 404
        assert client.get(
            f"/api/teaching-classes/{class_id}/teacher-homework", headers=outsider
        ).status_code == 403


def test_teacher_homework_empty_and_no_submission_states(tmp_path: Path) -> None:
    app, database = build_app(
        database_path=tmp_path / "teacher-homework-empty.db",
        jwt_secret="test-secret-with-enough-length",
    )
    with TestClient(app) as client:
        teacher, _ = register(client, "homework_empty_teacher", "teacher")
        class_id = create_class(client, teacher, "空作业统计班")
        empty = client.get(
            f"/api/teaching-classes/{class_id}/teacher-homework", headers=teacher
        )
        assert empty.status_code == 200
        assert empty.json()["data"] == {"items": [], "noData": True}

        seed_homework(database, class_id, due_at=int(time.time()) + 3600)
        no_submission = client.get(
            f"/api/teaching-classes/{class_id}/teacher-homework", headers=teacher
        )
        item = no_submission.json()["data"]["items"][0]
        assert item["submittedCount"] == 0
        assert item["submittedLearnerIds"] == []
        assert item["dataStatus"] == "no_submissions"
        assert item["correctRate"] is None
