"""知识库中心 v2 的 HTTP 公共 seam。"""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def register_teacher(client: TestClient, username: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "StrongPass123!",
            "displayName": username,
            "role": "teacher",
        },
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['data']['accessToken']}"}


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


def test_teacher_can_manage_a_reusable_knowledge_base_and_list_documents(tmp_path: Path) -> None:
    app = create_app(
        database_path=tmp_path / "knowledge-base-v2.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        headers = register_teacher(client, "kb_v2_teacher")
        created = client.post(
            "/api/knowledge-bases",
            headers=headers,
            json={"name": "具身智能入门", "description": "第一轮课程资料"},
        )
        assert created.status_code == 201
        knowledge_base_id = created.json()["data"]["id"]

        renamed = client.patch(
            f"/api/knowledge-bases/{knowledge_base_id}",
            headers=headers,
            json={"name": "具身智能入门（2026）"},
        )
        assert renamed.status_code == 200
        assert renamed.json()["data"]["name"] == "具身智能入门（2026）"

        uploaded = client.post(
            f"/api/knowledge-bases/{knowledge_base_id}/documents",
            headers=headers,
            files={"file": ("intro.md", "# 具身智能\n\n机器人通过感知和行动与环境交互。", "text/markdown")},
        )
        assert uploaded.status_code == 201
        document = uploaded.json()["data"]
        assert document["parseStatus"] == "not_started"
        assert document["version"] == 1

        documents = client.get(
            f"/api/knowledge-bases/{knowledge_base_id}/documents",
            headers=headers,
        )
        assert documents.status_code == 200
        assert documents.json()["data"]["items"][0]["id"] == document["id"]
        assert documents.json()["data"]["items"][0]["originalFilename"] == "intro.md"

        detail = client.get(
            f"/api/knowledge-bases/{knowledge_base_id}/documents/{document['id']}",
            headers=headers,
        )
        assert detail.status_code == 200
        assert detail.json()["data"]["title"] == "intro"

        archived = client.post(
            f"/api/knowledge-bases/{knowledge_base_id}/archive",
            headers=headers,
        )
        assert archived.status_code == 200
        assert archived.json()["data"]["status"] == "archived"


def test_document_edit_creates_a_new_version_and_invalidates_old_index(tmp_path: Path) -> None:
    app = create_app(
        database_path=tmp_path / "knowledge-base-document-version.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        headers = register_teacher(client, "kb_v2_document_teacher")
        knowledge_base_id = client.post(
            "/api/knowledge-bases",
            headers=headers,
            json={"name": "版本测试知识库"},
        ).json()["data"]["id"]
        document = client.post(
            f"/api/knowledge-bases/{knowledge_base_id}/documents",
            headers=headers,
            files={"file": ("lesson.md", "# 第一版\n\n旧内容。", "text/markdown")},
        ).json()["data"]
        document_id = document["id"]

        edited = client.patch(
            f"/api/knowledge-bases/{knowledge_base_id}/documents/{document_id}",
            headers=headers,
            json={"title": "第二课", "markdownContent": "# 第二版\n\n新内容。"},
        )
        assert edited.status_code == 200
        assert edited.json()["data"]["version"] == 2
        assert edited.json()["data"]["title"] == "第二课"
        assert edited.json()["data"]["parseStatus"] == "not_started"

        deleted = client.delete(
            f"/api/knowledge-bases/{knowledge_base_id}/documents/{document_id}",
            headers=headers,
        )
        assert deleted.status_code == 200
        assert deleted.json()["data"] is None
        assert client.get(
            f"/api/knowledge-bases/{knowledge_base_id}/documents/{document_id}",
            headers=headers,
        ).status_code == 404


def test_knowledge_base_supports_simple_and_advanced_segment_preview(tmp_path: Path) -> None:
    app = create_app(
        database_path=tmp_path / "knowledge-base-segments.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        headers = register_teacher(client, "kb_v2_segment_teacher")
        knowledge_base_id = client.post(
            "/api/knowledge-bases",
            headers=headers,
            json={"name": "分段测试知识库"},
        ).json()["data"]["id"]
        document = client.post(
            f"/api/knowledge-bases/{knowledge_base_id}/documents",
            headers=headers,
            files={"file": ("segment.md", "# 章节一\n\n第一段。第二段。\n\n## 章节二\n\n第三段。", "text/markdown")},
        ).json()["data"]
        settings = client.get(f"/api/knowledge-bases/{knowledge_base_id}/settings", headers=headers)
        assert settings.status_code == 200
        assert settings.json()["data"]["mode"] == "simple"
        assert settings.json()["data"]["maxCharacters"] == 2400
        assert settings.json()["data"]["overlapCharacters"] == 240

        preview = client.post(
            f"/api/knowledge-bases/{knowledge_base_id}/segments/preview",
            headers=headers,
            json={
                "documentId": document["id"],
                "mode": "advanced",
                "maxCharacters": 30,
                "overlapCharacters": 4,
                "separators": ["##"],
            },
        )
        assert preview.status_code == 200
        assert preview.json()["data"]["mode"] == "advanced"
        assert preview.json()["data"]["segments"]
        assert preview.json()["data"]["segments"][0]["titlePath"]

        rebuilt = client.post(
            f"/api/knowledge-bases/{knowledge_base_id}/segments/rebuild",
            headers=headers,
            json={
                "documentId": document["id"],
                "mode": "advanced",
                "maxCharacters": 30,
                "overlapCharacters": 4,
                "separators": ["##"],
            },
        )
        assert rebuilt.status_code == 200
        assert rebuilt.json()["data"]["chunkCount"] > 0

        segments = client.get(f"/api/knowledge-bases/{knowledge_base_id}/segments", headers=headers)
        assert segments.status_code == 200
        assert segments.json()["data"]["items"]


def test_advanced_second_level_heading_preview_remains_split_after_rebuild(tmp_path: Path) -> None:
    app = create_app(
        database_path=tmp_path / "knowledge-base-second-level-heading-rebuild.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        headers = register_teacher(client, "kb_v2_second_level_heading_teacher")
        knowledge_base_id = client.post(
            "/api/knowledge-bases",
            headers=headers,
            json={"name": "二级标题重建测试知识库"},
        ).json()["data"]["id"]
        document = client.post(
            f"/api/knowledge-bases/{knowledge_base_id}/documents",
            headers=headers,
            files={
                "file": (
                    "second-level.md",
                    "# 课程总览\n\n## 第一节\n\n第一节内容。\n\n## 第二节\n\n第二节内容。\n\n## 第三节\n\n第三节内容。",
                    "text/markdown",
                )
            },
        ).json()["data"]

        body = {
            "documentId": document["id"],
            "mode": "advanced",
            "maxCharacters": 2400,
            "overlapCharacters": 0,
            "separators": ["##"],
        }
        first_preview = client.post(
            f"/api/knowledge-bases/{knowledge_base_id}/segments/preview",
            headers=headers,
            json=body,
        )
        assert first_preview.status_code == 200
        assert len(first_preview.json()["data"]["segments"]) == 4

        rebuilt = client.post(
            f"/api/knowledge-bases/{knowledge_base_id}/segments/rebuild",
            headers=headers,
            json=body,
        )
        assert rebuilt.status_code == 200
        assert rebuilt.json()["data"]["chunkCount"] == 4

        second_preview = client.post(
            f"/api/knowledge-bases/{knowledge_base_id}/segments/preview",
            headers=headers,
            json=body,
        )
        assert second_preview.status_code == 200
        assert len(second_preview.json()["data"]["segments"]) == 4


def test_retrieval_test_returns_top_five_and_explicit_fallback_or_empty_state(tmp_path: Path) -> None:
    app = create_app(
        database_path=tmp_path / "knowledge-base-retrieval.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        headers = register_teacher(client, "kb_v2_retrieval_teacher")
        knowledge_base_id = client.post(
            "/api/knowledge-bases",
            headers=headers,
            json={"name": "召回测试知识库"},
        ).json()["data"]["id"]
        document = client.post(
            f"/api/knowledge-bases/{knowledge_base_id}/documents",
            headers=headers,
            files={"file": ("retrieval.md", "# 机器人感知\n\n视觉传感器帮助机器人理解环境。", "text/markdown")},
        ).json()["data"]
        rebuild_document(client, knowledge_base_id, document["id"], headers)

        result = client.post(
            f"/api/knowledge-bases/{knowledge_base_id}/retrieval-tests",
            headers=headers,
            json={"query": "机器人如何理解环境", "mode": "hybrid"},
        )
        assert result.status_code == 200
        payload = result.json()["data"]
        assert payload["topK"] == 5
        assert payload["hasResults"] is True
        assert len(payload["results"]) <= 5
        assert payload["results"][0]["score"] > 0
        assert payload["retrievalMode"] == "fts5"
        assert payload["fallbackReason"] == "EMBEDDING_NOT_CONFIGURED"

        empty = client.post(
            f"/api/knowledge-bases/{knowledge_base_id}/retrieval-tests",
            headers=headers,
            json={"query": "完全不存在的词", "mode": "keyword", "topK": 5, "minScore": 0.9},
        )
        assert empty.status_code == 200
        assert empty.json()["data"]["hasResults"] is False
        assert empty.json()["data"]["results"] == []


def test_teacher_can_import_selected_documents_from_multiple_sources_to_one_class_kb(tmp_path: Path) -> None:
    app = create_app(
        database_path=tmp_path / "knowledge-base-import.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        headers = register_teacher(client, "kb_v2_import_teacher")
        class_response = client.post(
            "/api/teaching-classes",
            headers=headers,
            json={"name": "具身智能试讲班", "joinPolicy": "free"},
        )
        class_id = class_response.json()["data"]["id"]

        source_ids: list[str] = []
        document_ids: list[str] = []
        for index in range(2):
            source_id = client.post(
                "/api/knowledge-bases",
                headers=headers,
                json={"name": f"来源知识库 {index}"},
            ).json()["data"]["id"]
            document = client.post(
                f"/api/knowledge-bases/{source_id}/documents",
                headers=headers,
                files={"file": (f"source-{index}.md", f"# 来源 {index}\n\n材料 {index}。", "text/markdown")},
            ).json()["data"]
            rebuild_document(client, source_id, document["id"], headers)
            source_ids.append(source_id)
            document_ids.append(document["id"])

        imported = client.post(
            "/api/knowledge-bases/imports",
            headers=headers,
            json={
                "targetClassId": class_id,
                "items": [
                    {"sourceKnowledgeBaseId": source_ids[0], "documentIds": [document_ids[0]]},
                    {"sourceKnowledgeBaseId": source_ids[1], "documentIds": [document_ids[1]]},
                ],
                "conflictStrategy": "skip",
            },
        )
        assert imported.status_code == 201
        payload = imported.json()["data"]
        assert len(payload["importedDocuments"]) == 2
        assert all(item["parseStatus"] == "completed" for item in payload["importedDocuments"])
        assert {item["sourceDocumentId"] for item in payload["importedDocuments"]} == set(document_ids)

        class_documents = client.get(
            f"/api/teaching-classes/{class_id}/knowledge-base",
            headers=headers,
        )
        assert class_documents.status_code == 200
        assert len(class_documents.json()["data"]["documents"]) == 2


def test_deleting_source_document_keeps_independent_class_copy(tmp_path: Path) -> None:
    app = create_app(
        database_path=tmp_path / "knowledge-base-delete-source.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        headers = register_teacher(client, "kb_v2_delete_source_teacher")
        class_id = client.post(
            "/api/teaching-classes",
            headers=headers,
            json={"name": "来源删除测试班", "joinPolicy": "free"},
        ).json()["data"]["id"]
        source_id = client.post(
            "/api/knowledge-bases",
            headers=headers,
            json={"name": "可删除来源知识库"},
        ).json()["data"]["id"]
        source_document = client.post(
            f"/api/knowledge-bases/{source_id}/documents",
            headers=headers,
            files={"file": ("source.md", "# 第一章\n\n## 第二节\n\n内容。", "text/markdown")},
        ).json()["data"]
        rebuild_document(client, source_id, source_document["id"], headers)
        imported = client.post(
            "/api/knowledge-bases/imports",
            headers=headers,
            json={
                "targetClassId": class_id,
                "items": [{"sourceKnowledgeBaseId": source_id, "documentIds": [source_document["id"]]}],
            },
        )
        assert imported.status_code == 201
        copied_document_id = imported.json()["data"]["importedDocuments"][0]["id"]

        deleted = client.delete(
            f"/api/knowledge-bases/{source_id}/documents/{source_document['id']}",
            headers=headers,
        )

        assert deleted.status_code == 200
        assert deleted.json()["data"] is None
        copied = client.get(
            f"/api/teaching-classes/{class_id}/knowledge-base",
            headers=headers,
        )
        assert copied.status_code == 200
        assert copied.json()["data"]["documents"][0]["id"] == copied_document_id


def test_preparation_session_selects_only_ready_class_knowledge_base_documents(tmp_path: Path) -> None:
    app = create_app(
        database_path=tmp_path / "knowledge-base-preparation-selection.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        headers = register_teacher(client, "kb_v2_preparation_teacher")
        class_id = client.post(
            "/api/teaching-classes",
            headers=headers,
            json={"name": "备课选文档班", "joinPolicy": "free"},
        ).json()["data"]["id"]
        source_id = client.post(
            "/api/knowledge-bases",
            headers=headers,
            json={"name": "备课来源"},
        ).json()["data"]["id"]
        source_document = client.post(
            f"/api/knowledge-bases/{source_id}/documents",
            headers=headers,
            files={"file": ("prep.md", "# 备课材料\n\n可用于划重点的内容。", "text/markdown")},
        ).json()["data"]
        rebuild_document(client, source_id, source_document["id"], headers)
        imported = client.post(
            "/api/knowledge-bases/imports",
            headers=headers,
            json={
                "targetClassId": class_id,
                "items": [{"sourceKnowledgeBaseId": source_id, "documentIds": [source_document["id"]]}],
            },
        )
        target_id = imported.json()["data"]["targetKnowledgeBase"]["id"]
        target_document_id = imported.json()["data"]["importedDocuments"][0]["id"]

        created = client.post(f"/api/teaching-classes/{class_id}/preparation-session", headers=headers)
        assert created.status_code == 201
        selected = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/documents",
            headers=headers,
            json={"documentIds": [target_document_id]},
        )
        assert selected.status_code == 200
        session = selected.json()["data"]
        assert session["knowledgeBaseId"] == target_id
        assert session["selectedDocumentIds"] == [target_document_id]
        assert session["parseStatus"] == "completed"

        paragraphs = client.get(
            f"/api/teaching-classes/{class_id}/preparation-session/parsed-paragraphs",
            headers=headers,
        )
        assert paragraphs.status_code == 200
        assert paragraphs.json()["data"]["paragraphs"]


def test_preparation_session_keeps_document_ownership_for_multiple_documents_and_can_exit(tmp_path: Path) -> None:
    app = create_app(
        database_path=tmp_path / "knowledge-base-preparation-multiple-documents.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        headers = register_teacher(client, "kb_v2_prep_multi_docs")
        class_id = client.post(
            "/api/teaching-classes",
            headers=headers,
            json={"name": "多文档备课班", "joinPolicy": "free"},
        ).json()["data"]["id"]
        source_id = client.post(
            "/api/knowledge-bases",
            headers=headers,
            json={"name": "多文档备课来源"},
        ).json()["data"]["id"]
        documents = []
        for index in range(2):
            documents.append(
                client.post(
                    f"/api/knowledge-bases/{source_id}/documents",
                    headers=headers,
                    files={
                        "file": (
                            f"lesson-{index}.md",
                            f"# 第 {index + 1} 份课件\n\n第 {index + 1} 份课件内容。",
                            "text/markdown",
                        )
                    },
                ).json()["data"]
            )
        for document in documents:
            rebuild_document(client, source_id, document["id"], headers)
        imported = client.post(
            "/api/knowledge-bases/imports",
            headers=headers,
            json={
                "targetClassId": class_id,
                "items": [{
                    "sourceKnowledgeBaseId": source_id,
                    "documentIds": [document["id"] for document in documents],
                }],
            },
        )
        assert imported.status_code == 201
        target_document_ids = [item["id"] for item in imported.json()["data"]["importedDocuments"]]

        assert client.post(f"/api/teaching-classes/{class_id}/preparation-session", headers=headers).status_code == 201
        selected = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/documents",
            headers=headers,
            json={"documentIds": target_document_ids},
        )
        assert selected.status_code == 200
        assert selected.json()["data"]["selectedDocumentIds"] == target_document_ids

        content = client.get(
            f"/api/teaching-classes/{class_id}/preparation-session/parsed-paragraphs-with-highlights",
            headers=headers,
        )
        assert content.status_code == 200
        paragraphs = content.json()["data"]["paragraphs"]
        assert {paragraph["documentId"] for paragraph in paragraphs} == set(target_document_ids)
        assert {paragraph["documentFilename"] for paragraph in paragraphs} == {"lesson-0.md", "lesson-1.md"}

        exited = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/documents",
            headers=headers,
            json={"documentIds": []},
        )
        assert exited.status_code == 200
        assert exited.json()["data"]["selectedDocumentIds"] == []
        assert exited.json()["data"]["parseStatus"] == "not_started"
