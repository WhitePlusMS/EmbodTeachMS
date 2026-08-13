"""备课端点的 OpenAPI 成功响应契约测试。"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.mark.parametrize(
    ("path", "method", "status_code", "schema_name"),
    [
        (
            "/api/teaching-classes/{class_id}/preparation-session",
            "post",
            "200",
            "ApiResponse_PreparationSessionView_",
        ),
        (
            "/api/teaching-classes/{class_id}/preparation-session",
            "post",
            "201",
            "ApiResponse_PreparationSessionView_",
        ),
        (
            "/api/teaching-classes/{class_id}/preparation-session",
            "get",
            "200",
            "ApiResponse_PreparationSessionView_",
        ),
        (
            "/api/teaching-classes/{class_id}/preparation-session/upload",
            "put",
            "200",
            "ApiResponse_PreparationSessionView_",
        ),
        (
            "/api/teaching-classes/{class_id}/preparation-session/parsed-paragraphs-with-highlights",
            "get",
            "200",
            "ApiResponse_PreparationSessionParsingResultWithHighlightsView_",
        ),
        (
            "/api/teaching-classes/{class_id}/preparation-session/highlights",
            "post",
            "201",
            "ApiResponse_HighlightView_",
        ),
        (
            "/api/teaching-classes/{class_id}/preparation-session/questions",
            "get",
            "200",
            "ApiResponse_QuestionListView_",
        ),
        (
            "/api/teaching-classes/{class_id}/preparation-session/questions",
            "post",
            "201",
            "ApiResponse_QuestionView_",
        ),
        (
            "/api/teaching-classes/{class_id}/preparation-session/questions/{question_id}",
            "put",
            "200",
            "ApiResponse_QuestionView_",
        ),
        (
            "/api/teaching-classes/{class_id}/preparation-session/questions/confirm",
            "post",
            "200",
            "ApiResponse_QuestionView_",
        ),
        (
            "/api/teaching-classes/{class_id}/preparation-session/questions/candidates",
            "post",
            "200",
            "ApiResponse_CandidateQuestionGenerationView_",
        ),
    ],
)
def test_preparation_success_response_keeps_payload_schema(
    tmp_path: Path,
    path: str,
    method: str,
    status_code: str,
    schema_name: str,
) -> None:
    app = create_app(
        database_path=tmp_path / "preparation-openapi.db",
        jwt_secret="test-secret-with-enough-length",
    )

    response_schema = app.openapi()["paths"][path][method]["responses"][status_code][
        "content"
    ]["application/json"]["schema"]

    assert response_schema == {
        "$ref": f"#/components/schemas/{schema_name}",
    }


def test_validation_errors_use_the_unified_response_contract(tmp_path: Path) -> None:
    app = create_app(
        database_path=tmp_path / "validation-openapi.db",
        jwt_secret="test-secret-with-enough-length",
    )

    openapi_schema = app.openapi()
    assert openapi_schema["paths"]["/api/auth/register"]["post"]["responses"]["422"][
        "content"
    ]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ApiResponse_NoneType_"
    }

    with TestClient(app) as client:
        response = client.post("/api/auth/register", json={})

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "REQUEST_VALIDATION_ERROR"
    assert body["data"] is None
    assert body["requestId"]
