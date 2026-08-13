"""教师查看学习者证据 HTTP 契约测试。"""

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
        json={"name": f"学习者证据测试班-{uuid.uuid4().hex[:6]}", "joinPolicy": join_policy},
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def join(client: TestClient, class_id: str, headers: dict[str, str]) -> None:
    response = client.post(f"/api/teaching-classes/{class_id}/join", headers=headers)
    assert response.status_code == 201


def create_join_request(client: TestClient, class_id: str, headers: dict[str, str]) -> str:
    response = client.post(
        f"/api/teaching-classes/{class_id}/join-request",
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["data"]["requestId"]


def resolve_join_request(
    client: TestClient, request_id: str, teacher_headers: dict[str, str], status: str
) -> None:
    response = client.patch(
        f"/api/teaching-classes/join-requests/{request_id}/resolve",
        headers=teacher_headers,
        json={"status": status},
    )
    assert response.status_code == 200


def assert_learner_list_shape(data: dict) -> None:
    """验证学习者列表响应形状"""
    assert isinstance(data["items"], list)

    for item in data["items"]:
        assert set(item) == {
            "learnerId",
            "displayName",
            "completionRate",
            "weakestKnowledgePoint",
            "simulationStatus"
        }
        # 验证simulationStatus固定为no_data
        assert item["simulationStatus"] == "no_data"


def assert_learner_detail_shape(data: dict) -> None:
    """验证学习者详情响应形状"""
    assert set(data) == {
        "learnerId",
        "displayName",
        "completionStats",
        "masterySummary",
        "simulationStatus"
    }

    # 验证completionStats形状
    assert set(data["completionStats"]) == {
        "totalContents",
        "completedContents",
        "completionRate"
    }

    # 验证masterySummary形状（复用现有MasterySummaryView）
    assert set(data["masterySummary"]) == {
        "status",
        "message",
        "totalKnowledgePoints",
        "levelDistribution",
        "knowledgePoints",
        "nextSuggestion"
    }

    # 验证knowledgePoints中每个知识点的形状
    for kp in data["masterySummary"]["knowledgePoints"]:
        assert set(kp) == {
            "knowledgePoint",
            "masteryLevel",
            "weightedScore",
            "recentEvidenceCount",
            "firstCorrectCount",
            "levelChange",
            "latestEvidence"
        }

        # 验证latestEvidence形状（可能为None）
        if kp["latestEvidence"] is not None:
            assert set(kp["latestEvidence"]) == {
                "questionId",
                "resultType",
                "createdAt"
            }

    # 验证simulationStatus固定为no_data
    assert data["simulationStatus"] == "no_data"

    # 验证响应中没有原始小D字段
    forbidden_fields = {"chat", "prompt", "content", "raw"}
    def check_no_forbidden_fields(obj, path=""):
        if isinstance(obj, dict):
            for key in obj:
                full_path = f"{path}.{key}" if path else key
                assert key not in forbidden_fields, f"发现禁止字段: {full_path}"
                check_no_forbidden_fields(obj[key], full_path)
        elif isinstance(obj, list):
            for item in obj:
                check_no_forbidden_fields(item, path)

    check_no_forbidden_fields(data)


def test_teacher_get_learner_list_empty_class(tmp_path: Path) -> None:
    """测试空班级的学习者列表返回空数组"""
    app = create_app(
        database_path=tmp_path / "learner-list-empty.db",
        jwt_secret="test-secret-with-enough-length",
    )
    with TestClient(app) as client:
        teacher, _ = register(client, "teacher_empty", "teacher")
        class_id = create_class(client, teacher)

        response = client.get(
            f"/api/teaching-classes/{class_id}/learners",
            headers=teacher,
        )

        assert response.status_code == 200
        assert response.json()["code"] == "LEARNERS_LISTED"
        data = response.json()["data"]

        assert_learner_list_shape(data)
        assert data["items"] == []


def test_teacher_get_learner_list_with_members(tmp_path: Path) -> None:
    """测试有正式成员的学习者列表"""
    app, database = build_app(
        database_path=tmp_path / "learner-list-members.db",
        jwt_secret="test-secret-with-enough-length",
    )
    with TestClient(app) as client:
        teacher, teacher_id = register(client, "teacher_members", "teacher")
        learners = [
            register(client, f"learner_member_{i}", "learner")
            for i in range(3)
        ]
        class_id = create_class(client, teacher)

        # 学习者自由加入
        for learner_headers, _ in learners:
            join(client, class_id, learner_headers)

        # 创建已发布内容
        now = int(time.time())
        content_id = str(uuid.uuid4())
        with database.connect() as connection:
            connection.execute(
                """
                INSERT INTO course_contents
                (id, class_id, content_type, publication_status, title, content, created_at, updated_at)
                VALUES (?, ?, 'knowledge_module', 'published', '测试内容', '正文', ?, ?)
                """,
                (content_id, class_id, now, now),
            )

            # 为第一个学习者创建完成记录
            connection.execute(
                """
                INSERT INTO course_content_completions
                (id, learner_id, class_id, content_id, completed_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (str(uuid.uuid4()), learners[0][1], class_id, content_id, now, now),
            )

            # 为所有学习者创建基准练习记录（用于掌握度计算）
            for i, (_, learner_id) in enumerate(learners):
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
                    (
                        str(uuid.uuid4()),
                        learner_id,
                        class_id,
                        content_id,
                        i % 2 == 0,
                        "first_correct" if i % 2 == 0 else "final_wrong",
                        now,
                        now,
                    ),
                )

        response = client.get(
            f"/api/teaching-classes/{class_id}/learners",
            headers=teacher,
        )

        assert response.status_code == 200
        assert response.json()["code"] == "LEARNERS_LISTED"
        data = response.json()["data"]

        assert_learner_list_shape(data)
        assert len(data["items"]) == 3

        # 验证学习者按确定性排序（按加入时间倒序）
        learner_ids = [item["learnerId"] for item in data["items"]]
        expected_learner_ids = [learner[1] for learner in learners]
        assert set(learner_ids) == set(expected_learner_ids)

        # 验证第一个学习者有完成记录
        completed_learner = next(
            item for item in data["items"] if item["learnerId"] == learners[0][1]
        )
        assert completed_learner["completionRate"] > 0


def test_teacher_get_learner_list_excludes_pending_requests(tmp_path: Path) -> None:
    """测试学习者列表不包含待审批用户"""
    app = create_app(
        database_path=tmp_path / "learner-list-pending.db",
        jwt_secret="test-secret-with-enough-length",
    )
    with TestClient(app) as client:
        teacher, _ = register(client, "teacher_pending", "teacher")
        member, member_id = register(client, "learner_member", "learner")
        pending, _ = register(client, "learner_pending", "learner")

        class_id = create_class(client, teacher)

        # 正式成员先入班，再切换审批制创建待审批申请。
        join(client, class_id, member)
        policy_response = client.patch(
            f"/api/teaching-classes/{class_id}/join-policy",
            headers=teacher,
            json={"joinPolicy": "approval"},
        )
        assert policy_response.status_code == 200

        # 另一个学习者提交申请（待审批）
        create_join_request(client, class_id, pending)

        response = client.get(
            f"/api/teaching-classes/{class_id}/learners",
            headers=teacher,
        )

        assert response.status_code == 200
        data = response.json()["data"]

        assert_learner_list_shape(data)
        assert len(data["items"]) == 1
        assert data["items"][0]["learnerId"] == member_id


def test_teacher_get_learner_detail(tmp_path: Path) -> None:
    """测试获取学习者详情"""
    app, database = build_app(
        database_path=tmp_path / "learner-detail.db",
        jwt_secret="test-secret-with-enough-length",
    )
    with TestClient(app) as client:
        teacher, teacher_id = register(client, "teacher_detail", "teacher")
        learner, learner_id = register(client, "learner_detail", "learner")
        class_id = create_class(client, teacher)

        join(client, class_id, learner)

        # 创建学习事实
        now = int(time.time())
        content_id = str(uuid.uuid4())
        with database.connect() as connection:
            # 创建已发布内容
            connection.execute(
                """
                INSERT INTO course_contents
                (id, class_id, content_type, publication_status, title, content, created_at, updated_at)
                VALUES (?, ?, 'knowledge_module', 'published', '测试内容', '知识点:知识点1', ?, ?)
                """,
                (content_id, class_id, now, now),
            )

            # 创建完成记录
            connection.execute(
                """
                INSERT INTO course_content_completions
                (id, learner_id, class_id, content_id, completed_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (str(uuid.uuid4()), learner_id, class_id, content_id, now, now),
            )

            # 创建基准练习记录
            connection.execute(
                """
                INSERT INTO baseline_practice_runs
                (id, learner_id, class_id, content_id, status, first_attempt_answers,
                 second_attempt_answers, final_answers, is_correct, correct_answers,
                 explanation, question_type, difficulty, knowledge_points, source,
                 score, result_type, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'completed', '[]', '[]', '[0]', ?, '[0]',
                        '解析', 'multiple_choice', 'easy', '["知识点1"]', '来源',
                        1, 'first_correct', ?, ?)
                """,
                (str(uuid.uuid4()), learner_id, class_id, content_id, True, now, now),
            )

        response = client.get(
            f"/api/teaching-classes/{class_id}/learners/{learner_id}",
            headers=teacher,
        )

        assert response.status_code == 200
        assert response.json()["code"] == "LEARNER_DETAIL_FETCHED"
        data = response.json()["data"]

        assert_learner_detail_shape(data)
        assert data["learnerId"] == learner_id
        assert data["displayName"] == "learner_detail"
        assert data["completionStats"]["totalContents"] == 1
        assert data["completionStats"]["completedContents"] == 1
        assert data["completionStats"]["completionRate"] == 1.0
        assert data["simulationStatus"] == "no_data"


def test_teacher_get_learner_detail_pending_request_forbidden(tmp_path: Path) -> None:
    """测试待审批用户详情不可读"""
    app = create_app(
        database_path=tmp_path / "learner-detail-pending-forbidden.db",
        jwt_secret="test-secret-with-enough-length",
    )
    with TestClient(app) as client:
        teacher, _ = register(client, "teacher_pending_forbidden", "teacher")
        pending, pending_id = register(client, "learner_pending_forbidden", "learner")

        class_id = create_class(client, teacher, join_policy="approval")

        # 提交申请但未审批
        create_join_request(client, class_id, pending)

        response = client.get(
            f"/api/teaching-classes/{class_id}/learners/{pending_id}",
            headers=teacher,
        )

        assert response.status_code == 404
        assert response.json()["code"] == "RESOURCE_NOT_FOUND"


def test_teacher_get_learner_detail_cross_class_forbidden(tmp_path: Path) -> None:
    """测试跨班学习者详情不可读"""
    app = create_app(
        database_path=tmp_path / "learner-detail-cross-class.db",
        jwt_secret="test-secret-with-enough-length",
    )
    with TestClient(app) as client:
        teacher_a, _ = register(client, "teacher_a", "teacher")
        teacher_b, _ = register(client, "teacher_b", "teacher")
        learner, learner_id = register(client, "learner_cross", "learner")

        class_a_id = create_class(client, teacher_a)
        class_b_id = create_class(client, teacher_b)

        # 学习者加入班级A
        join(client, class_a_id, learner)

        # 教师B尝试访问班级A的学习者
        response = client.get(
            f"/api/teaching-classes/{class_a_id}/learners/{learner_id}",
            headers=teacher_b,
        )

        assert response.status_code == 404
        assert response.json()["code"] == "RESOURCE_NOT_FOUND"


def test_teacher_get_learner_detail_other_class_member_forbidden(tmp_path: Path) -> None:
    """测试其他班正式成员详情不可读"""
    app = create_app(
        database_path=tmp_path / "learner-detail-other-class.db",
        jwt_secret="test-secret-with-enough-length",
    )
    with TestClient(app) as client:
        teacher, _ = register(client, "teacher_other_class", "teacher")
        member_a, member_a_id = register(client, "member_a", "learner")
        member_b, member_b_id = register(client, "member_b", "learner")

        class_a_id = create_class(client, teacher)
        class_b_id = create_class(client, teacher)

        # 学习者A加入班级A
        join(client, class_a_id, member_a)
        # 学习者B加入班级B
        join(client, class_b_id, member_b)

        # 教师尝试在班级A访问班级B的学习者
        response = client.get(
            f"/api/teaching-classes/{class_a_id}/learners/{member_b_id}",
            headers=teacher,
        )

        assert response.status_code == 404
        assert response.json()["code"] == "RESOURCE_NOT_FOUND"


def test_teacher_get_learner_detail_learner_forbidden(tmp_path: Path) -> None:
    """测试学习者访问学习者详情返回403"""
    app = create_app(
        database_path=tmp_path / "learner-detail-learner-forbidden.db",
        jwt_secret="test-secret-with-enough-length",
    )
    with TestClient(app) as client:
        teacher, _ = register(client, "teacher_learner_forbidden", "teacher")
        learner_a, learner_a_id = register(client, "learner_a", "learner")
        learner_b, learner_b_id = register(client, "learner_b", "learner")

        class_id = create_class(client, teacher)

        # 两个学习者都加入班级
        join(client, class_id, learner_a)
        join(client, class_id, learner_b)

        # 学习者A尝试访问学习者B的详情
        response = client.get(
            f"/api/teaching-classes/{class_id}/learners/{learner_b_id}",
            headers=learner_a,
        )

        assert response.status_code == 403
        assert response.json()["code"] == "AUTH_ROLE_FORBIDDEN"


def test_teacher_get_learner_detail_no_evidence(tmp_path: Path) -> None:
    """测试无学习证据的学习者详情"""
    app = create_app(
        database_path=tmp_path / "learner-detail-no-evidence.db",
        jwt_secret="test-secret-with-enough-length",
    )
    with TestClient(app) as client:
        teacher, _ = register(client, "teacher_no_evidence", "teacher")
        learner, learner_id = register(client, "learner_no_evidence", "learner")
        class_id = create_class(client, teacher)

        join(client, class_id, learner)

        response = client.get(
            f"/api/teaching-classes/{class_id}/learners/{learner_id}",
            headers=teacher,
        )

        assert response.status_code == 200
        data = response.json()["data"]

        assert_learner_detail_shape(data)
        assert data["learnerId"] == learner_id
        assert data["completionStats"]["totalContents"] == 0
        assert data["completionStats"]["completedContents"] == 0
        assert data["completionStats"]["completionRate"] == 0.0
        assert data["masterySummary"]["totalKnowledgePoints"] == 0
        assert data["masterySummary"]["knowledgePoints"] == []
        assert data["simulationStatus"] == "no_data"


def test_teacher_get_learner_detail_ordered_by_join_time(tmp_path: Path) -> None:
    """测试学习者列表按加入时间倒序排序"""
    app = create_app(
        database_path=tmp_path / "learner-list-order.db",
        jwt_secret="test-secret-with-enough-length",
    )
    with TestClient(app) as client:
        teacher, _ = register(client, "teacher_order", "teacher")

        # 创建学习者并记录创建时间
        learners = []
        for i in range(3):
            # 按顺序创建，但加入时间会倒序
            learner, learner_id = register(client, f"learner_order_{i}", "learner")
            learners.append((learner, learner_id))

        class_id = create_class(client, teacher)

        # 按顺序加入，确保后加入的排在前面
        for learner_headers, _ in learners:
            join(client, class_id, learner_headers)

        response = client.get(
            f"/api/teaching-classes/{class_id}/learners",
            headers=teacher,
        )

        assert response.status_code == 200
        data = response.json()["data"]

        # 验证顺序：后加入的排在前面
        learner_ids = [item["learnerId"] for item in data["items"]]
        expected_order = [learner[1] for learner in reversed(learners)]
        assert learner_ids == expected_order
