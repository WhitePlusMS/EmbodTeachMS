"""教师课程管理 HTTP 回归测试。"""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def _register_teacher(client: TestClient, username: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "StrongPass123!",
            "displayName": "测试教师",
            "role": "teacher",
        },
    )
    assert response.status_code == 201
    access_token = response.json()["data"]["accessToken"]
    return {"Authorization": f"Bearer {access_token}"}


def test_teacher_can_rename_owned_class_over_http(tmp_path: Path) -> None:
    """重命名接口必须命中真实路由并返回统一响应 DTO。"""
    app = create_app(
        database_path=tmp_path / "class-management.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        headers = _register_teacher(client, "teacher_rename")
        created = client.post(
            "/api/teaching-classes",
            headers=headers,
            json={"name": "旧课程名称", "joinPolicy": "free"},
        )
        assert created.status_code == 201
        class_id = created.json()["data"]["id"]

        renamed = client.patch(
            f"/api/teaching-classes/{class_id}/name",
            headers=headers,
            json={"name": "新课程名称"},
        )

        assert renamed.status_code == 200
        assert renamed.json()["code"] == "TEACHING_CLASS_RENAMED"
        assert renamed.json()["data"]["id"] == class_id
        assert renamed.json()["data"]["name"] == "新课程名称"

