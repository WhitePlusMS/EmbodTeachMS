from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def register(client: TestClient, username: str, role: str = "teacher") -> dict[str, str]:
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
    return {"Authorization": f"Bearer {response.json()['data']['accessToken']}"}


def create_class(client: TestClient, headers: dict[str, str], name: str) -> str:
    response = client.post(
        "/api/teaching-classes",
        headers=headers,
        json={"name": name, "joinPolicy": "free"},
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def rebuild_document(client: TestClient, knowledge_base_id: str, document_id: str, headers: dict[str, str]) -> None:
    response = client.post(
        f"/api/knowledge-bases/{knowledge_base_id}/segments/rebuild",
        headers=headers,
        json={
            "documentId": document_id,
            "mode": "simple",
            "maxCharacters": 2400,
            "overlapCharacters": 240,
            "separators": ["#"],
        },
    )
    assert response.status_code == 200


def test_knowledge_base_copy_parse_and_search_are_class_scoped(tmp_path: Path) -> None:
    app = create_app(
        database_path=tmp_path / "knowledge-base.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        headers = register(client, "kb_teacher")
        class_a = create_class(client, headers, "知识库班级 A")
        class_b = create_class(client, headers, "知识库班级 B")

        created = client.post(
            "/api/knowledge-bases",
            headers=headers,
            json={"name": "机器人学基础", "description": "可复用课件"},
        )
        assert created.status_code == 201
        source_id = created.json()["data"]["id"]

        source_upload = client.post(
            f"/api/knowledge-bases/{source_id}/documents",
            headers=headers,
            files={"file": ("shared.md", "# 共享课件\n\n机器人基础知识。", "text/markdown")},
        )
        assert source_upload.status_code == 201
        rebuild_document(client, source_id, source_upload.json()["data"]["id"], headers)

        copied_a = client.post(
            f"/api/knowledge-bases/{source_id}/copies",
            headers=headers,
            json={"targetClassId": class_a},
        )
        assert copied_a.status_code == 201
        copy_a_id = copied_a.json()["data"]["id"]

        copied_b = client.post(
            f"/api/knowledge-bases/{source_id}/copies",
            headers=headers,
            json={"targetClassId": class_b, "name": "机器人学基础 B"},
        )
        assert copied_b.status_code == 201

        upload = client.post(
            f"/api/knowledge-bases/{copy_a_id}/documents",
            headers=headers,
            files={"file": ("kinematics.md", "# 运动学\n\n正向运动学描述机器人位姿。", "text/markdown")},
        )
        assert upload.status_code == 201
        assert upload.json()["data"]["parseStatus"] == "not_started"

        rebuild_document(client, copy_a_id, upload.json()["data"]["id"], headers)

        workspace = client.get(f"/api/teaching-classes/{class_a}/knowledge-base", headers=headers)
        assert workspace.status_code == 200
        assert len(workspace.json()["data"]["documents"]) == 2

        search = client.post(
            f"/api/knowledge-bases/{copy_a_id}/search",
            headers=headers,
            json={"query": "运动学"},
        )
        assert search.status_code == 200
        assert search.json()["data"]["hasResults"] is True
        assert search.json()["data"]["results"][0]["documentFilename"] == "kinematics.md"

        publication = client.post(
            f"/api/knowledge-bases/{copy_a_id}/publish",
            headers=headers,
        )
        assert publication.status_code == 201
        assert publication.json()["data"]["version"] == 1
        assert len(publication.json()["data"]["contentIds"]) == 2

        published_contents = client.get(
            f"/api/teaching-classes/{class_a}/published-contents",
            headers=headers,
        )
        assert published_contents.status_code == 200
        assert len(published_contents.json()["data"]["items"]) == 2

        other_workspace = client.get(f"/api/teaching-classes/{class_b}/knowledge-base", headers=headers)
        assert other_workspace.status_code == 200
        assert len(other_workspace.json()["data"]["documents"]) == 1


def test_knowledge_base_requires_teacher_and_hides_missing_class(tmp_path: Path) -> None:
    app = create_app(
        database_path=tmp_path / "knowledge-base-permission.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        learner_headers = register(client, "kb_learner", "learner")
        response = client.get(
            "/api/teaching-classes/not-a-class/knowledge-base",
            headers=learner_headers,
        )
        assert response.status_code == 403
        assert response.json()["code"] == "AUTH_ROLE_FORBIDDEN"


def test_markdown_build_failure_is_persistent_and_retry_keeps_document_identity(tmp_path: Path) -> None:
    app = create_app(
        database_path=tmp_path / "knowledge-base-failure.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        headers = register(client, "kb_failure_teacher")
        created = client.post(
            "/api/knowledge-bases",
            headers=headers,
            json={"name": "失败重试知识库"},
        )
        knowledge_base_id = created.json()["data"]["id"]

        unsupported = client.post(
            f"/api/knowledge-bases/{knowledge_base_id}/documents",
            headers=headers,
            files={"file": ("notes.pdf", b"not supported", "application/pdf")},
        )
        assert unsupported.status_code == 400
        assert unsupported.json()["code"] == "FILE_FORMAT_UNSUPPORTED"

        uploaded = client.post(
            f"/api/knowledge-bases/{knowledge_base_id}/documents",
            headers=headers,
            files={"file": ("broken.md", b"\xff\xfe", "text/markdown")},
        )
        document_id = uploaded.json()["data"]["id"]
        assert uploaded.json()["data"]["parseStatus"] == "not_started"

        preview = client.post(
            f"/api/knowledge-bases/{knowledge_base_id}/segments/preview",
            headers=headers,
            json={
                "documentId": document_id,
                "mode": "simple",
                "maxCharacters": 2400,
                "overlapCharacters": 240,
                "separators": ["#"],
            },
        )
        assert preview.status_code == 409

        knowledge_base = client.get(
            f"/api/knowledge-bases/{knowledge_base_id}", headers=headers
        )
        assert knowledge_base.json()["data"]["documentCount"] == 1

        retry = client.post(
            f"/api/knowledge-bases/documents/{document_id}/retry",
            headers=headers,
        )
        assert retry.status_code == 200
        assert retry.json()["data"]["id"] == document_id
        assert retry.json()["data"]["errorMessage"] == "Markdown 文件编码错误，无法读取"
