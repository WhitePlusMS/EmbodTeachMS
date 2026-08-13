"""隐私安全班级聚合 HTTP 契约测试。"""

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
        json={"name": f"聚合测试班-{uuid.uuid4().hex[:6]}", "joinPolicy": join_policy},
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def join(client: TestClient, class_id: str, headers: dict[str, str]) -> None:
    response = client.post(f"/api/teaching-classes/{class_id}/join", headers=headers)
    assert response.status_code == 201


def assert_privacy_shape(data: dict) -> None:
    serialized_keys = {key.lower() for key in data}
    forbidden = {"learnerid", "name", "username", "account", "rank", "formalgrade", "score"}
    assert serialized_keys.isdisjoint(forbidden)
    assert set(data) == {
        "status",
        "message",
        "totalMembers",
        "contentCompletionRate",
        "atLeastOneCompleted",
        "masteryDistribution",
        "simulationStatus",
        "insufficientSample",
        "noData",
    }


def test_member_gets_insufficient_sample_without_personal_details(tmp_path: Path) -> None:
    app = create_app(
        database_path=tmp_path / "aggregate-small.db",
        jwt_secret="test-secret-with-enough-length",
    )
    with TestClient(app) as client:
        teacher, _ = register(client, "aggregate_teacher_small", "teacher")
        learner, _ = register(client, "aggregate_learner_small", "learner")
        class_id = create_class(client, teacher)
        join(client, class_id, learner)

        response = client.get(
            f"/api/teaching-classes/{class_id}/aggregate-stats",
            headers=learner,
        )

        assert response.status_code == 200
        assert response.json()["code"] == "INSUFFICIENT_SAMPLE"
        data = response.json()["data"]
        assert data["insufficientSample"] is True
        assert data["masteryDistribution"] is None
        assert data["simulationStatus"] == "no_data"
        assert_privacy_shape(data)


def test_aggregate_uses_only_current_class_members(tmp_path: Path) -> None:
    app, database = build_app(
        database_path=tmp_path / "aggregate-success.db",
        jwt_secret="test-secret-with-enough-length",
    )
    with TestClient(app) as client:
        teacher, _ = register(client, "aggregate_teacher_success", "teacher")
        members = [
            register(client, f"aggregate_member_{index}", "learner")
            for index in range(3)
        ]
        outsider, outsider_id = register(client, "aggregate_outsider", "learner")
        class_id = create_class(client, teacher)
        for headers, _ in members:
            join(client, class_id, headers)
        other_class_id = create_class(client, teacher)

        now = int(time.time())
        content_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        with database.connect() as connection:
            for index, content_id in enumerate(content_ids):
                connection.execute(
                    """
                    INSERT INTO course_contents
                    (id, class_id, content_type, publication_status, title, content, created_at, updated_at)
                    VALUES (?, ?, 'knowledge_module', 'published', ?, ?, ?, ?)
                    """,
                    (content_id, class_id, f"内容{index}", "正文", now, now),
                )
            connection.execute(
                """
                INSERT INTO course_content_completions
                (id, learner_id, class_id, content_id, completed_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (str(uuid.uuid4()), members[0][1], class_id, content_ids[0], now, now),
            )
            # 外部学习者伪造的其他班事实不得进入当前班聚合。
            connection.execute(
                """
                INSERT INTO course_content_completions
                (id, learner_id, class_id, content_id, completed_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (str(uuid.uuid4()), outsider_id, other_class_id, content_ids[1], now, now),
            )

        response = client.get(
            f"/api/teaching-classes/{class_id}/aggregate-stats",
            headers=members[0][0],
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["status"] == "success"
        assert data["totalMembers"] == 3
        assert data["atLeastOneCompleted"] == 1
        assert data["contentCompletionRate"] == 1 / 6
        assert sum(data["masteryDistribution"].values()) == 3
        assert data["simulationStatus"] == "no_data"
        assert_privacy_shape(data)


def test_non_member_pending_and_cross_class_member_are_forbidden(tmp_path: Path) -> None:
    app = create_app(
        database_path=tmp_path / "aggregate-attacks.db",
        jwt_secret="test-secret-with-enough-length",
    )
    with TestClient(app) as client:
        teacher, _ = register(client, "aggregate_teacher_attacks", "teacher")
        outsider, _ = register(client, "aggregate_plain_outsider", "learner")
        pending, _ = register(client, "aggregate_pending", "learner")
        cross_member, _ = register(client, "aggregate_cross_member", "learner")

        target_class_id = create_class(client, teacher, join_policy="approval")
        pending_response = client.post(
            f"/api/teaching-classes/{target_class_id}/join-request",
            headers=pending,
        )
        assert pending_response.status_code == 201

        other_class_id = create_class(client, teacher)
        join(client, other_class_id, cross_member)

        for headers in (outsider, pending, cross_member):
            response = client.get(
                f"/api/teaching-classes/{target_class_id}/aggregate-stats",
                headers=headers,
            )
            assert response.status_code == 403
            assert response.json()["code"] == "CLASS_MEMBERSHIP_REQUIRED"
