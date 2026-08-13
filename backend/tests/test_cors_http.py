from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def test_frontend_can_preflight_delete_document(tmp_path: Path) -> None:
    """文档删除的跨域预检必须允许 DELETE 和前端请求头。"""
    frontend_origin = "http://127.0.0.1:5173"
    app = create_app(
        database_path=tmp_path / "cors.db",
        jwt_secret="test-secret-with-enough-length",
        allowed_origins=(frontend_origin,),
    )

    with TestClient(app) as client:
        response = client.options(
            "/api/knowledge-bases/kb-1/documents/document-1",
            headers={
                "Origin": frontend_origin,
                "Access-Control-Request-Method": "DELETE",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == frontend_origin
    assert "DELETE" in response.headers["access-control-allow-methods"]
