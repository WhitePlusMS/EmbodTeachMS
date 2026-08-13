from pathlib import Path

from fastapi.testclient import TestClient

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


def test_empty_teaching_classes_list_for_teacher(tmp_path: Path) -> None:
    """教师初始状态教学班列表为空。"""
    app = create_app(
        database_path=tmp_path / "empty_classes.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher01")

        # 获取教学班列表
        response = client.get("/api/teaching-classes", headers=teacher_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == "TEACHING_CLASSES_LISTED"
        assert body["data"] == {"items": []}
        assert body["requestId"] == response.headers["X-Request-Id"]


def test_create_and_list_teaching_classes_with_three_policies(tmp_path: Path) -> None:
    """创建三种加入策略的教学班并验证列表。"""
    app = create_app(
        database_path=tmp_path / "three_policies.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_policies")

        # 创建三种策略的教学班
        policies = ["free", "approval", "closed"]
        for i, policy in enumerate(policies):
            response = client.post(
                "/api/teaching-classes",
                headers=teacher_headers,
                json={
                    "name": f"测试班级{i+1}",
                    "joinPolicy": policy,
                },
            )
            assert response.status_code == 201
            body = response.json()
            assert body["code"] == "TEACHING_CLASS_CREATED"
            assert body["data"]["name"] == f"测试班级{i+1}"
            assert body["data"]["joinPolicy"] == policy
            assert body["data"]["memberCount"] == 0  # 新班memberCount=0
            assert "ownerId" not in body["data"]  # 无ownerId
            assert body["requestId"] == response.headers["X-Request-Id"]

        # 获取教学班列表并验证
        response = client.get("/api/teaching-classes", headers=teacher_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == "TEACHING_CLASSES_LISTED"
        assert len(body["data"]["items"]) == 3

        classes_by_name = {
            class_data["name"]: class_data
            for class_data in body["data"]["items"]
        }
        for i, policy in enumerate(policies):
            class_data = classes_by_name[f"测试班级{i+1}"]
            assert class_data["id"]
            assert class_data["joinPolicy"] == policy
            assert class_data["memberCount"] == 0
            assert "ownerId" not in class_data
            assert class_data["createdAt"]
            assert class_data["updatedAt"]


def test_get_teaching_class_persists_after_reload(tmp_path: Path) -> None:
    """教学班详情在重新加载后保持持久性。"""
    app = create_app(
        database_path=tmp_path / "persistence.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_persist")

        # 创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "持久测试班",
                "joinPolicy": "free",
            },
        )
        assert response.status_code == 201
        created_class = response.json()["data"]
        class_id = created_class["id"]

        # 修改加入策略为approval
        patch_response = client.patch(
            f"/api/teaching-classes/{class_id}/join-policy",
            headers=teacher_headers,
            json={"joinPolicy": "approval"},
        )
        assert patch_response.status_code == 200
        assert patch_response.json()["code"] == "TEACHING_CLASS_UPDATED"

        # 获取教学班详情
        response = client.get(f"/api/teaching-classes/{class_id}", headers=teacher_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == "TEACHING_CLASS_FETCHED"
        assert body["data"]["id"] == class_id
        assert body["data"]["name"] == "持久测试班"
        assert body["data"]["joinPolicy"] == "approval"  # 验证修改后的策略
        assert body["requestId"] == response.headers["X-Request-Id"]

        # 重新获取验证持久性
        response_again = client.get(f"/api/teaching-classes/{class_id}", headers=teacher_headers)
        assert response_again.status_code == 200
        assert response_again.json()["data"] == body["data"]


def test_learner_cannot_create_or_access_teaching_class(tmp_path: Path) -> None:
    """学习者无权创建或访问教学班。"""
    app = create_app(
        database_path=tmp_path / "learner_forbidden.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        learner_headers = register_user(client, "learner01", "learner")

        # 尝试创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=learner_headers,
            json={
                "name": "测试班级",
                "joinPolicy": "free",
            },
        )
        assert response.status_code == 403
        assert response.json()["code"] == "AUTH_ROLE_FORBIDDEN"
        assert response.json()["requestId"] == response.headers["X-Request-Id"]

        # 尝试获取教学班列表
        response = client.get("/api/teaching-classes", headers=learner_headers)
        assert response.status_code == 403
        assert response.json()["code"] == "AUTH_ROLE_FORBIDDEN"
        assert response.json()["requestId"] == response.headers["X-Request-Id"]


def test_teacher_cannot_access_another_teacher_class(tmp_path: Path) -> None:
    """教师A不能访问教师B的教学班。"""
    app = create_app(
        database_path=tmp_path / "teacher_isolation.db",
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

        # 教师B尝试获取教师A的班级
        response = client.get(f"/api/teaching-classes/{class_id}", headers=teacher_b_headers)
        assert response.status_code == 404
        assert response.json()["code"] == "RESOURCE_NOT_FOUND"
        assert response.json()["requestId"] == response.headers["X-Request-Id"]

        # 教师B尝试修改教师A的班级加入策略
        response = client.patch(
            f"/api/teaching-classes/{class_id}/join-policy",
            headers=teacher_b_headers,
            json={"joinPolicy": "closed"},
        )
        assert response.status_code == 404
        assert response.json()["code"] == "RESOURCE_NOT_FOUND"
        assert response.json()["requestId"] == response.headers["X-Request-Id"]


def test_blank_class_name_validation(tmp_path: Path) -> None:
    """名称先清理首尾空白，纯空白仍返回 422。"""
    app = create_app(
        database_path=tmp_path / "validation.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_validation")

        normalized = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={"name": "  机器人系统 2 班  ", "joinPolicy": "free"},
        )
        assert normalized.status_code == 201
        assert normalized.json()["data"]["name"] == "机器人系统 2 班"

        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "   ",
                "joinPolicy": "free",
            },
        )
        assert response.status_code == 422
        assert response.json()["code"] == "REQUEST_VALIDATION_ERROR"
        assert response.json()["requestId"] == response.headers["X-Request-Id"]


def test_all_responses_include_request_id(tmp_path: Path) -> None:
    """所有响应都包含requestId。"""
    app = create_app(
        database_path=tmp_path / "request_id.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_rid")

        # 创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "ID测试班",
                "joinPolicy": "free",
            },
        )
        assert response.status_code == 201
        assert response.json()["requestId"] == response.headers["X-Request-Id"]

        class_id = response.json()["data"]["id"]

        # 获取列表
        response = client.get("/api/teaching-classes", headers=teacher_headers)
        assert response.status_code == 200
        assert response.json()["code"] == "TEACHING_CLASSES_LISTED"
        assert response.json()["requestId"] == response.headers["X-Request-Id"]

        # 获取详情
        response = client.get(f"/api/teaching-classes/{class_id}", headers=teacher_headers)
        assert response.status_code == 200
        assert response.json()["code"] == "TEACHING_CLASS_FETCHED"
        assert response.json()["requestId"] == response.headers["X-Request-Id"]

        # 修改加入策略
        response = client.patch(
            f"/api/teaching-classes/{class_id}/join-policy",
            headers=teacher_headers,
            json={"joinPolicy": "approval"},
        )
        assert response.status_code == 200
        assert response.json()["code"] == "TEACHING_CLASS_UPDATED"
        assert response.json()["requestId"] == response.headers["X-Request-Id"]

        # 无效ID获取
        response = client.get("/api/teaching-classes/invalid-id", headers=teacher_headers)
        assert response.status_code == 404
        assert response.json()["code"] == "RESOURCE_NOT_FOUND"
        assert response.json()["requestId"] == response.headers["X-Request-Id"]
