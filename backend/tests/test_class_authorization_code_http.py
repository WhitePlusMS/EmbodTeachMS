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


def create_class(client, teacher_headers: dict, name: str, join_policy: str = "free") -> str:
    """辅助函数：创建教学班并返回班级ID"""
    response = client.post(
        "/api/teaching-classes",
        json={
            "name": name,
            "joinPolicy": join_policy,
        },
        headers=teacher_headers,
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def test_teacher_can_create_and_get_authorization_code(tmp_path: Path) -> None:
    """教师可以创建和获取授权码"""
    app = create_app(
        database_path=tmp_path / "auth_code.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher01")
        class_id = create_class(client, teacher_headers, "测试班级")

        # 获取授权码（应该返回空）
        response = client.get(f"/api/teaching-classes/{class_id}/authorization-code", headers=teacher_headers)
        assert response.status_code == 200
        assert response.json()["data"] is None

        # 创建授权码
        response = client.put(
            f"/api/teaching-classes/{class_id}/authorization-code",
            json={
                "enabled": True,
                "expiresAt": None,
            },
            headers=teacher_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["classId"] == class_id
        assert data["enabled"] is True
        assert data["expiresAt"] is None
        assert len(data["code"]) == 12

        # 再次获取授权码
        response = client.get(f"/api/teaching-classes/{class_id}/authorization-code", headers=teacher_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["classId"] == class_id
        assert data["enabled"] is True


def test_teacher_can_update_authorization_code(tmp_path: Path) -> None:
    """教师可以更新授权码"""
    app = create_app(
        database_path=tmp_path / "update_auth_code.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher01")
        class_id = create_class(client, teacher_headers, "测试班级")

        # 创建授权码
        response = client.put(
            f"/api/teaching-classes/{class_id}/authorization-code",
            json={"enabled": True, "expiresAt": None},
            headers=teacher_headers,
        )
        assert response.status_code == 200
        original_code = response.json()["data"]["code"]

        # 更新授权码
        response = client.put(
            f"/api/teaching-classes/{class_id}/authorization-code",
            json={"enabled": False, "expiresAt": 9999999999},
            headers=teacher_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["classId"] == class_id
        assert data["enabled"] is False
        assert data["expiresAt"] == 9999999999
        assert data["code"] == original_code  # 代码不应该改变


def test_learner_can_join_class_with_valid_authorization_code(tmp_path: Path) -> None:
    """学习者可以使用有效授权码加入班级"""
    app = create_app(
        database_path=tmp_path / "join_with_code.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher01")
        learner_headers = register_user(client, "learner01", "learner")

        # 创建不同策略的班级
        free_class_id = create_class(client, teacher_headers, "自由班级", "free")
        approval_class_id = create_class(client, teacher_headers, "审批班级", "approval")
        closed_class_id = create_class(client, teacher_headers, "关闭班级", "closed")

        # 为每个班级创建授权码
        for class_id in [free_class_id, approval_class_id, closed_class_id]:
            response = client.put(
                f"/api/teaching-classes/{class_id}/authorization-code",
                json={"enabled": True, "expiresAt": None},
                headers=teacher_headers,
            )
            assert response.status_code == 200
            auth_code = response.json()["data"]["code"]

            # 学习者使用授权码加入
            response = client.post(
                "/api/teaching-classes/join-by-authorization-code",
                json={"code": auth_code},
                headers=learner_headers,
            )
            assert response.status_code == 201
            data = response.json()["data"]
            assert data["classId"] == class_id
            assert data["learnerId"]
            assert data["isNewMember"] is True

        # 验证学习者已加入所有班级
        response = client.get("/api/teaching-classes/mine", headers=learner_headers)
        assert response.status_code == 200
        assert len(response.json()["data"]["items"]) == 3


def test_authorization_code_overrides_rejected_join_request(tmp_path: Path) -> None:
    """有效邀请码可以绕过历史拒绝直接加入教学班。"""
    app = create_app(
        database_path=tmp_path / "authorization_code_after_rejection.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_code_priority")
        learner_headers = register_user(client, "learner_code_priority", "learner")
        class_id = create_class(client, teacher_headers, "邀请码优先班级", "approval")

        response = client.put(
            f"/api/teaching-classes/{class_id}/authorization-code",
            json={"enabled": True, "expiresAt": None},
            headers=teacher_headers,
        )
        assert response.status_code == 200
        authorization_code = response.json()["data"]["code"]

        response = client.post(
            f"/api/teaching-classes/{class_id}/join-request",
            headers=learner_headers,
        )
        assert response.status_code == 201
        request_id = response.json()["data"]["requestId"]

        response = client.patch(
            f"/api/teaching-classes/join-requests/{request_id}/resolve",
            headers=teacher_headers,
            json={"status": "rejected"},
        )
        assert response.status_code == 200

        response = client.post(
            "/api/teaching-classes/join-by-authorization-code",
            json={"code": authorization_code},
            headers=learner_headers,
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["classId"] == class_id
        assert data["isNewMember"] is True

        response = client.get("/api/teaching-classes/mine", headers=learner_headers)
        assert response.status_code == 200
        assert [item["id"] for item in response.json()["data"]["items"]] == [class_id]


def test_authorization_code_validation(tmp_path: Path) -> None:
    """授权码验证逻辑"""
    app = create_app(
        database_path=tmp_path / "validation.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher01")
        learner_headers = register_user(client, "learner01", "learner")
        class_id = create_class(client, teacher_headers, "测试班级")

        # 创建授权码
        response = client.put(
            f"/api/teaching-classes/{class_id}/authorization-code",
            json={"enabled": True, "expiresAt": None},
            headers=teacher_headers,
        )
        assert response.status_code == 200
        valid_code = response.json()["data"]["code"]

        # 测试无效授权码
        response = client.post(
            "/api/teaching-classes/join-by-authorization-code",
            json={"code": "INVALIDCODE123"},
            headers=learner_headers,
        )
        assert response.status_code == 400
        assert response.json()["code"] == "CLASS_AUTHORIZATION_CODE_INVALID"

        # 禁用授权码
        response = client.put(
            f"/api/teaching-classes/{class_id}/authorization-code",
            json={"enabled": False, "expiresAt": None},
            headers=teacher_headers,
        )
        assert response.status_code == 200

        # 测试禁用的授权码
        response = client.post(
            "/api/teaching-classes/join-by-authorization-code",
            json={"code": valid_code},
            headers=learner_headers,
        )
        assert response.status_code == 400
        assert response.json()["code"] == "CLASS_AUTHORIZATION_CODE_INVALID"


def test_expired_authorization_code(tmp_path: Path) -> None:
    """过期授权码验证"""
    current_time = [1_000]
    app = create_app(
        database_path=tmp_path / "expired.db",
        jwt_secret="test-secret-with-enough-length",
        now_provider=lambda: current_time[0],
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher01")
        learner_headers = register_user(client, "learner01", "learner")
        class_id = create_class(client, teacher_headers, "测试班级")

        # 授权码创建时仍有效，随后时间推进到失效时刻。
        response = client.put(
            f"/api/teaching-classes/{class_id}/authorization-code",
            json={"enabled": True, "expiresAt": current_time[0] + 1},
            headers=teacher_headers,
        )
        assert response.status_code == 200
        expired_code = response.json()["data"]["code"]
        current_time[0] += 1

        # 测试过期授权码
        response = client.post(
            "/api/teaching-classes/join-by-authorization-code",
            json={"code": expired_code},
            headers=learner_headers,
        )
        assert response.status_code == 400
        assert response.json()["code"] == "CLASS_AUTHORIZATION_CODE_INVALID"


def test_idempotent_membership_with_authorization_code(tmp_path: Path) -> None:
    """授权码加入的幂等性"""
    app = create_app(
        database_path=tmp_path / "idempotent.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher01")
        learner_headers = register_user(client, "learner01", "learner")
        class_id = create_class(client, teacher_headers, "测试班级")

        # 创建授权码
        response = client.put(
            f"/api/teaching-classes/{class_id}/authorization-code",
            json={"enabled": True, "expiresAt": None},
            headers=teacher_headers,
        )
        assert response.status_code == 200
        auth_code = response.json()["data"]["code"]

        # 第一次加入
        response = client.post(
            "/api/teaching-classes/join-by-authorization-code",
            json={"code": auth_code},
            headers=learner_headers,
        )
        assert response.status_code == 201
        assert response.json()["data"]["isNewMember"] is True

        # 第二次加入（幂等）
        response = client.post(
            "/api/teaching-classes/join-by-authorization-code",
            json={"code": auth_code},
            headers=learner_headers,
        )
        assert response.status_code == 201
        assert response.json()["data"]["isNewMember"] is False

        # 验证只加入了一次
        response = client.get("/api/teaching-classes/mine", headers=learner_headers)
        assert response.status_code == 200
        assert len(response.json()["data"]["items"]) == 1


def test_authorization_code_creation_validation(tmp_path: Path) -> None:
    """授权码创建时的验证"""
    app = create_app(
        database_path=tmp_path / "creation_validation.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher01")
        class_id = create_class(client, teacher_headers, "测试班级")

        # 测试过期时间无效
        response = client.put(
            f"/api/teaching-classes/{class_id}/authorization-code",
            json={"enabled": True, "expiresAt": 0},  # 无效的过期时间
            headers=teacher_headers,
        )
        assert response.status_code == 422
        assert response.json()["code"] == "REQUEST_VALIDATION_ERROR"
