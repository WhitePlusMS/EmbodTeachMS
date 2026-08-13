from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def test_learner_can_register_login_and_read_current_session(tmp_path: Path) -> None:
    """验证认证主路径，只通过 HTTP 公共接口观察行为。"""
    app = create_app(
        database_path=tmp_path / "auth.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        register_response = client.post(
            "/api/auth/register",
            json={
                "username": "learner01",
                "password": "StrongPass123!",
                "displayName": "林晓",
                "role": "learner",
            },
        )
        assert register_response.status_code == 201
        register_body = register_response.json()
        assert register_body["code"] == "AUTH_REGISTERED"
        assert register_body["message"] == "注册成功"
        assert register_body["data"]["user"] == {
            "id": register_body["data"]["user"]["id"],
            "username": "learner01",
            "displayName": "林晓",
            "role": "learner",
        }
        assert register_body["data"]["accessToken"]
        assert register_body["requestId"]

        login_response = client.post(
            "/api/auth/login",
            json={"username": "learner01", "password": "StrongPass123!"},
        )
        assert login_response.status_code == 200
        login_body = login_response.json()
        assert login_body["code"] == "AUTH_LOGGED_IN"
        assert login_body["data"]["user"]["role"] == "learner"

        me_response = client.get(
            "/api/auth/me",
            headers={
                "Authorization": f"Bearer {login_body['data']['accessToken']}"
            },
        )
        assert me_response.status_code == 200
        assert me_response.json()["data"] == login_body["data"]["user"]


def test_users_can_only_open_the_workspace_for_their_fixed_role(
    tmp_path: Path,
) -> None:
    """角色工作台由后端授权，前端隐藏导航不是权限边界。"""
    app = create_app(
        database_path=tmp_path / "roles.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        learner = client.post(
            "/api/auth/register",
            json={
                "username": "learner02",
                "password": "StrongPass123!",
                "displayName": "林晓",
                "role": "learner",
            },
        ).json()["data"]
        teacher = client.post(
            "/api/auth/register",
            json={
                "username": "teacher01",
                "password": "StrongPass123!",
                "displayName": "周老师",
                "role": "teacher",
            },
        ).json()["data"]

        learner_headers = {
            "Authorization": f"Bearer {learner['accessToken']}"
        }
        teacher_headers = {
            "Authorization": f"Bearer {teacher['accessToken']}"
        }

        learner_workspace = client.get(
            "/api/workspaces/learner", headers=learner_headers
        )
        assert learner_workspace.status_code == 200
        assert learner_workspace.json()["data"] == {
            "role": "learner",
            "title": "我的课程",
            "navigation": ["我的课程"],
        }

        teacher_workspace = client.get(
            "/api/workspaces/teacher", headers=teacher_headers
        )
        assert teacher_workspace.status_code == 200
        assert teacher_workspace.json()["data"] == {
            "role": "teacher",
            "title": "我的课程",
            "navigation": ["我的课程"],
        }

        forbidden = client.get(
            "/api/workspaces/teacher", headers=learner_headers
        )
        assert forbidden.status_code == 403
        assert forbidden.json()["code"] == "AUTH_ROLE_FORBIDDEN"
        assert forbidden.json()["message"] == "当前角色无权访问该工作台"
        assert forbidden.json()["requestId"]


def test_logout_revokes_the_server_session_immediately(tmp_path: Path) -> None:
    """退出后的旧令牌必须立即失效，不能继续读取用户数据。"""
    app = create_app(
        database_path=tmp_path / "logout.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        auth_payload = client.post(
            "/api/auth/register",
            json={
                "username": "learner03",
                "password": "StrongPass123!",
                "displayName": "陈屿",
                "role": "learner",
            },
        ).json()["data"]
        headers = {
            "Authorization": f"Bearer {auth_payload['accessToken']}"
        }

        logout_response = client.post("/api/auth/logout", headers=headers)
        assert logout_response.status_code == 200
        assert logout_response.json()["code"] == "AUTH_LOGGED_OUT"

        expired_session = client.get("/api/auth/me", headers=headers)
        assert expired_session.status_code == 401
        assert expired_session.json() == {
            "code": "AUTH_SESSION_INVALID",
            "message": "登录状态已失效，请重新登录",
            "data": None,
            "requestId": expired_session.json()["requestId"],
        }


def test_auth_failures_use_stable_codes_and_the_unified_envelope(
    tmp_path: Path,
) -> None:
    app = create_app(
        database_path=tmp_path / "errors.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        registration = {
            "username": "teacher02",
            "password": "StrongPass123!",
            "displayName": "王老师",
            "role": "teacher",
        }
        assert client.post("/api/auth/register", json=registration).status_code == 201

        duplicate = client.post("/api/auth/register", json=registration)
        assert duplicate.status_code == 409
        assert duplicate.json()["code"] == "AUTH_USERNAME_EXISTS"

        invalid_credentials = client.post(
            "/api/auth/login",
            json={"username": "teacher02", "password": "WrongPassword!"},
        )
        assert invalid_credentials.status_code == 401
        assert invalid_credentials.json()["code"] == "AUTH_INVALID_CREDENTIALS"

        invalid_role = client.post(
            "/api/auth/register",
            json={**registration, "username": "invalid-role", "role": "admin"},
        )
        assert invalid_role.status_code == 422
        assert invalid_role.json()["code"] == "REQUEST_VALIDATION_ERROR"

        not_found = client.get("/api/does-not-exist")
        assert not_found.status_code == 404
        assert not_found.json()["code"] == "RESOURCE_NOT_FOUND"

        for response in (
            duplicate,
            invalid_credentials,
            invalid_role,
            not_found,
        ):
            body = response.json()
            assert set(body) == {"code", "message", "data", "requestId"}
            assert body["data"] is None
            assert body["requestId"] == response.headers["X-Request-Id"]


def test_session_expires_exactly_after_eight_hours(tmp_path: Path) -> None:
    """通过可控系统时钟验证会话边界，不读取数据库或令牌内部结构。"""
    current_time = [1_000_000]
    app = create_app(
        database_path=tmp_path / "expiry.db",
        jwt_secret="test-secret-with-enough-length",
        now_provider=lambda: current_time[0],
    )

    with TestClient(app) as client:
        payload = client.post(
            "/api/auth/register",
            json={
                "username": "expiry_user",
                "password": "StrongPass123!",
                "displayName": "时钟测试",
                "role": "learner",
            },
        ).json()["data"]
        headers = {"Authorization": f"Bearer {payload['accessToken']}"}

        current_time[0] += 8 * 60 * 60 - 1
        assert client.get("/api/auth/me", headers=headers).status_code == 200

        current_time[0] += 1
        expired = client.get("/api/auth/me", headers=headers)
        assert expired.status_code == 401
        assert expired.json()["code"] == "AUTH_SESSION_INVALID"


def test_unhandled_failures_still_use_the_unified_envelope(tmp_path: Path) -> None:
    app = create_app(
        database_path=tmp_path / "unhandled.db",
        jwt_secret="test-secret-with-enough-length",
    )

    @app.get("/api/test/unhandled")
    def raise_unhandled_error() -> None:
        raise RuntimeError("test-only failure")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/test/unhandled")

    assert response.status_code == 500
    assert response.json() == {
        "code": "INTERNAL_ERROR",
        "message": "服务暂时不可用，请稍后重试",
        "data": None,
        "requestId": response.json()["requestId"],
    }
