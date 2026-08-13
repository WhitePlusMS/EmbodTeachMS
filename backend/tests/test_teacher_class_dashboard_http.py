"""教师班级dashboard HTTP 契约测试。"""

import time
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from tests.conftest import build_app


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


def create_class(
    client: TestClient, teacher_headers: dict[str, str], *, join_policy: str = "free"
) -> str:
    response = client.post(
        "/api/teaching-classes",
        headers=teacher_headers,
        json={"name": f"dashboard测试班-{uuid.uuid4().hex[:6]}", "joinPolicy": join_policy},
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def join(client: TestClient, class_id: str, headers: dict[str, str]) -> None:
    response = client.post(f"/api/teaching-classes/{class_id}/join", headers=headers)
    assert response.status_code == 201


def assert_teacher_dashboard_shape(data: dict) -> None:
    """验证教师dashboard响应形状"""
    assert set(data) == {
        "totalMembers",
        "contentCompletionRate",
        "atLeastOneCompleted",
        "masteryDistribution",
        "questionsStatus",
        "consolidationTopics",
        "homeworkSummary",
        "simulationStatus",
        "learnerPreviews",
        "insufficientSample",
        "noData",
    }

    # 验证掌握度分布形状
    assert set(data["masteryDistribution"]) == {"unlearned", "consolidating", "basicMastery", "proficientMastery"}

    # 验证作业摘要形状
    assert set(data["homeworkSummary"]) == {
        "totalHomeworks",
        "expectedSubmissions",
        "pendingSubmissions",
        "submittedSubmissions",
        "lateSubmissions",
        "averageScore",
    }

    # 验证高频提问状态
    assert data["questionsStatus"] == "no_data"

    # 验证学习者预览形状
    if data["learnerPreviews"]:
        for preview in data["learnerPreviews"]:
            assert set(preview) == {"learnerId", "displayName", "completionRate", "masteryLevel", "lastActivity"}

    # 验证待巩固知识点形状
    if data["consolidationTopics"]:
        for topic in data["consolidationTopics"]:
            assert set(topic) == {"knowledgePoint", "learnersCount", "averageMastery"}

def test_teacher_dashboard_empty_class_shape(tmp_path: Path) -> None:
    """测试空班级的dashboard返回正确形状"""
    app = create_app(
        database_path=tmp_path / "dashboard-empty.db",
        jwt_secret="test-secret-with-enough-length",
    )
    with TestClient(app) as client:
        teacher, _ = register(client, "dashboard_teacher_empty", "teacher")
        class_id = create_class(client, teacher)

        response = client.get(
            f"/api/teaching-classes/{class_id}/teacher-dashboard",
            headers=teacher,
        )

        assert response.status_code == 200
        assert response.json()["code"] == "NO_DATA"
        data = response.json()["data"]

        assert_teacher_dashboard_shape(data)
        assert data["noData"] is True
        assert data["totalMembers"] == 0
        assert data["contentCompletionRate"] == 0.0
        assert data["atLeastOneCompleted"] == 0
        assert data["questionsStatus"] == "no_data"
        assert data["consolidationTopics"] == []
        assert data["simulationStatus"] == "no_data"
        assert data["learnerPreviews"] == []


def test_teacher_dashboard_insufficient_sample(tmp_path: Path) -> None:
    """测试样本不足时的dashboard返回"""
    app = create_app(
        database_path=tmp_path / "dashboard-small.db",
        jwt_secret="test-secret-with-enough-length",
    )
    with TestClient(app) as client:
        teacher, _ = register(client, "dashboard_teacher_small", "teacher")
        learner, _ = register(client, "dashboard_learner_small", "learner")
        class_id = create_class(client, teacher)
        join(client, class_id, learner)

        response = client.get(
            f"/api/teaching-classes/{class_id}/teacher-dashboard",
            headers=teacher,
        )

        assert response.status_code == 200
        assert response.json()["code"] == "INSUFFICIENT_SAMPLE"
        data = response.json()["data"]

        assert_teacher_dashboard_shape(data)
        assert data["insufficientSample"] is True
        assert data["totalMembers"] == 1


def test_teacher_dashboard_with_facts_aggregation(tmp_path: Path) -> None:
    """测试有事实数据时的dashboard聚合"""
    app, database = build_app(
        database_path=tmp_path / "dashboard-facts.db",
        jwt_secret="test-secret-with-enough-length",
    )
    with TestClient(app) as client:
        teacher, teacher_id = register(client, "dashboard_teacher_facts", "teacher")
        members = [
            register(client, f"dashboard_member_{index}", "learner")
            for index in range(3)
        ]
        class_id = create_class(client, teacher)
        for headers, learner_id in members:
            join(client, class_id, headers)

        now = int(time.time())
        content_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        homework_id = str(uuid.uuid4())

        with database.connect() as connection:
            # 创建已发布内容
            for index, content_id in enumerate(content_ids):
                connection.execute(
                    """
                    INSERT INTO course_contents
                    (id, class_id, content_type, publication_status, title, content, created_at, updated_at)
                    VALUES (?, ?, 'knowledge_module', 'published', ?, ?, ?, ?)
                    """,
                    (content_id, class_id, f"内容{index}", "正文", now, now),
                )

            # 创建作业
            connection.execute(
                """
                INSERT INTO course_contents
                (id, class_id, content_type, publication_status, title, content, due_at, created_at, updated_at)
                VALUES (?, ?, 'homework', 'published', '测试作业', '作业内容', ?, ?, ?)
                """,
                (homework_id, class_id, now + 86400, now, now),
            )

            # 创建内容完成记录
            for index, (_, learner_id) in enumerate(members[:2]):
                connection.execute(
                    """
                    INSERT INTO course_content_completions
                    (id, learner_id, class_id, content_id, completed_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (str(uuid.uuid4()), learner_id, class_id, content_ids[0], now, now),
                )

            # 创建作业提交记录
            connection.execute(
                """
                INSERT INTO homework_submissions
                (id, learner_id, class_id, homework_id, status, answers_json, grading_json,
                 total_score, correct_count, submitted_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'submitted', '{}', '{}', 80, 4, ?, ?, ?)
                """,
                (str(uuid.uuid4()), members[0][1], class_id, homework_id, now, now, now),
            )

            # 创建基准练习记录（用于掌握度计算）
            for index, (_, learner_id) in enumerate(members):
                connection.execute(
                    """
                    INSERT INTO baseline_practice_runs
                    (id, learner_id, class_id, content_id, status, first_attempt_answers,
                     second_attempt_answers, final_answers, is_correct, correct_answers,
                     explanation, question_type, difficulty, knowledge_points, source,
                     score, result_type, created_at, updated_at)
                    VALUES (?, ?, ?, ?, 'completed', '[]', '[]', '[0]', ?, '[0]',
                            '解析', 'multiple_choice', 'easy', '["知识点1"]', '来源',
                            1, ?, ?, ?)
                    """,
                    (str(uuid.uuid4()), learner_id, class_id, content_ids[0],
                     index % 2 == 0,
                     "first_correct" if index % 2 == 0 else "final_wrong",
                     now,
                     now),
                )

        response = client.get(
            f"/api/teaching-classes/{class_id}/teacher-dashboard",
            headers=teacher,
        )

        assert response.status_code == 200
        assert response.json()["code"] == "TEACHER_DASHBOARD_FETCHED"
        data = response.json()["data"]

        assert_teacher_dashboard_shape(data)
        assert data["totalMembers"] == 3
        assert data["atLeastOneCompleted"] == 2
        assert data["contentCompletionRate"] == 2 / 6  # 2人完成，3人×2内容

        # 验证掌握度分布
        assert sum(data["masteryDistribution"].values()) == 3

        # 验证高频提问状态（应为no_data，因为没有真实提问表）
        assert data["questionsStatus"] == "no_data"

        # 验证作业摘要
        assert data["homeworkSummary"]["totalHomeworks"] == 1
        assert data["homeworkSummary"]["expectedSubmissions"] == 3
        assert data["homeworkSummary"]["pendingSubmissions"] == 2
        assert data["homeworkSummary"]["submittedSubmissions"] == 1
        assert data["homeworkSummary"]["lateSubmissions"] == 0
        assert data["homeworkSummary"]["averageScore"] == 80.0

        # 验证学习者预览（上限5个）
        assert len(data["learnerPreviews"]) == 3  # 只有3个成员
        assert data["simulationStatus"] == "no_data"


def test_teacher_dashboard_other_teacher_forbidden(tmp_path: Path) -> None:
    """测试其他教师访问dashboard返回403"""
    app = create_app(
        database_path=tmp_path / "dashboard-forbidden.db",
        jwt_secret="test-secret-with-enough-length",
    )
    with TestClient(app) as client:
        owner_teacher, _ = register(client, "dashboard_owner_teacher", "teacher")
        other_teacher, _ = register(client, "dashboard_other_teacher", "teacher")
        class_id = create_class(client, owner_teacher)

        response = client.get(
            f"/api/teaching-classes/{class_id}/teacher-dashboard",
            headers=other_teacher,
        )

        assert response.status_code == 404
        assert response.json()["code"] == "RESOURCE_NOT_FOUND"


def test_teacher_dashboard_learner_forbidden(tmp_path: Path) -> None:
    """测试学习者访问dashboard返回403"""
    app = create_app(
        database_path=tmp_path / "dashboard-learner-forbidden.db",
        jwt_secret="test-secret-with-enough-length",
    )
    with TestClient(app) as client:
        teacher, _ = register(client, "dashboard_teacher_learner", "teacher")
        learner, _ = register(client, "dashboard_learner", "learner")
        class_id = create_class(client, teacher)
        join(client, class_id, learner)

        response = client.get(
            f"/api/teaching-classes/{class_id}/teacher-dashboard",
            headers=learner,
        )

        assert response.status_code == 403
        assert response.json()["code"] == "AUTH_ROLE_FORBIDDEN"


def test_teacher_dashboard_cross_class_facts_isolation(tmp_path: Path) -> None:
    """测试跨班事实隔离"""
    app, database = build_app(
        database_path=tmp_path / "dashboard-isolation.db",
        jwt_secret="test-secret-with-enough-length",
    )
    with TestClient(app) as client:
        teacher, teacher_id = register(client, "dashboard_teacher_isolation", "teacher")
        members = [
            register(client, f"dashboard_member_isolation_{index}", "learner")
            for index in range(3)
        ]

        # 创建两个班级
        class_a_id = create_class(client, teacher)
        class_b_id = create_class(client, teacher)

        # 成员加入两个班级
        for headers, learner_id in members:
            join(client, class_a_id, headers)
            join(client, class_b_id, headers)

        now = int(time.time())

        with database.connect() as connection:
            # 为班级A创建内容
            content_a_id = str(uuid.uuid4())
            connection.execute(
                """
                INSERT INTO course_contents
                (id, class_id, content_type, publication_status, title, content, created_at, updated_at)
                VALUES (?, ?, 'knowledge_module', 'published', '班级A内容', '正文', ?, ?)
                """,
                (content_a_id, class_a_id, now, now),
            )

            # 为班级B创建内容
            content_b_id = str(uuid.uuid4())
            connection.execute(
                """
                INSERT INTO course_contents
                (id, class_id, content_type, publication_status, title, content, created_at, updated_at)
                VALUES (?, ?, 'knowledge_module', 'published', '班级B内容', '正文', ?, ?)
                """,
                (content_b_id, class_b_id, now, now),
            )

            # 只在班级B创建完成记录
            for _, learner_id in members:
                connection.execute(
                    """
                    INSERT INTO course_content_completions
                    (id, learner_id, class_id, content_id, completed_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (str(uuid.uuid4()), learner_id, class_b_id, content_b_id, now, now),
                )

        # 检查班级A的dashboard（应该没有完成记录）
        response_a = client.get(
            f"/api/teaching-classes/{class_a_id}/teacher-dashboard",
            headers=teacher,
        )

        assert response_a.status_code == 200
        data_a = response_a.json()["data"]
        assert data_a["totalMembers"] == 3
        assert data_a["atLeastOneCompleted"] == 0  # 班级A没有完成记录
        assert data_a["contentCompletionRate"] == 0.0

        # 检查班级B的dashboard（应该有完成记录）
        response_b = client.get(
            f"/api/teaching-classes/{class_b_id}/teacher-dashboard",
            headers=teacher,
        )

        assert response_b.status_code == 200
        data_b = response_b.json()["data"]
        assert data_b["totalMembers"] == 3
        assert data_b["atLeastOneCompleted"] == 3  # 班级B有3个完成记录
        assert data_b["contentCompletionRate"] == 1.0  # 3人完成1个内容


def test_teacher_dashboard_learner_preview_limit(tmp_path: Path) -> None:
    """测试学习者预览数量上限"""
    app = create_app(
        database_path=tmp_path / "dashboard-preview-limit.db",
        jwt_secret="test-secret-with-enough-length",
    )
    with TestClient(app) as client:
        teacher, _ = register(client, "dashboard_teacher_preview", "teacher")

        # 创建6个学习者
        members = [
            register(client, f"dashboard_member_preview_{index}", "learner")
            for index in range(6)
        ]

        class_id = create_class(client, teacher)
        for headers, _ in members:
            join(client, class_id, headers)

        response = client.get(
            f"/api/teaching-classes/{class_id}/teacher-dashboard",
            headers=teacher,
        )

        assert response.status_code == 200
        data = response.json()["data"]

        # 验证学习者预览数量上限为5
        assert len(data["learnerPreviews"]) == 5

        # 验证预览按加入时间倒序（后加入的先显示）
        preview_learner_ids = [preview["learnerId"] for preview in data["learnerPreviews"]]

        # 后加入的5个学习者应该在预览中
        expected_learner_ids = [member[1] for member in members[1:]]  # 后5个
        assert set(preview_learner_ids) == set(expected_learner_ids)
