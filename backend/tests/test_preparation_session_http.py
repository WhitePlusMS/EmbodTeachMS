import json
import logging
import time
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.llm_gateway import StaticChatGateway
from app.document_parsing.models import ParsingResult, ParsedParagraph, ParsingStatus
from tests.conftest import build_app, seed_preparation_state

class StubCourseContentParsing:
    """按预设顺序返回解析结果的 fake，配合同步执行器替代 patch 与 sleep。"""

    def __init__(self, results: list[ParsingResult]) -> None:
        self._results = list(results)

    def parse(self, file_path, file_format) -> ParsingResult:
        if len(self._results) > 1:
            return self._results.pop(0)
        return self._results[0]


def test_candidate_questions_use_configured_gateway_and_persist_review_state(tmp_path: Path) -> None:
    generated = json.dumps(
        {
            "items": [
                {
                    "type": "single_choice",
                    "stem": "反馈控制的核心作用是什么？",
                    "options": ["根据误差调整输出", "忽略传感器", "固定输出", "关闭执行器"],
                    "answers": [0],
                    "knowledgePoints": ["反馈控制"],
                    "highlightSourceIds": ["highlight-1"],
                    "hint": "关注误差。",
                    "explanation": "反馈控制根据目标与实际输出的误差调整控制量。",
                }
            ]
        },
        ensure_ascii=False,
    )
    app, database = build_app(
        tmp_path / "candidate-questions-llm.db",
        jwt_secret="test-secret-with-enough-length",
        chat_gateway=StaticChatGateway(generated),
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "candidate_llm_teacher")
        created = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={"name": "候选题模型班", "joinPolicy": "free"},
        )
        class_id = created.json()["data"]["id"]
        session = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session",
            headers=teacher_headers,
        ).json()["data"]
        with database.connect() as connection:
            seed_preparation_state(
                connection,
                session["id"],
                segments=[(0, "text", "反馈控制根据误差调整执行器输出。")],
                highlights=[
                    {
                        "id": "highlight-1",
                        "paragraphOrdinal": 0,
                        "startOffset": 0,
                        "endOffset": 4,
                    }
                ],
            )

        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/questions/candidates",
            headers=teacher_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["status"] == "success"
        assert data["source"] == "demo"
        assert len(data["items"]) == 1
        assert data["items"][0]["reviewStatus"] == "candidate"
        assert data["items"][0]["highlightSourceIds"] == ["highlight-1"]

        listed = client.get(
            f"/api/teaching-classes/{class_id}/preparation-session/questions",
            headers=teacher_headers,
        )
        assert len(listed.json()["data"]["items"]) == 1


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


def multipart_file(upload_data: dict) -> dict:
    """构造真实 multipart 上传体，文件头与声明格式保持一致。"""
    filename = upload_data["originalFilename"]
    size = upload_data["fileSizeBytes"]
    prefix = b"%PDF-" if filename.endswith(".pdf") else b"PK\x03\x04" if filename.endswith(".docx") else b"# markdown\n"
    return {"file": (filename, prefix + b"x" * max(0, size - len(prefix)))}


def test_create_and_get_preparation_session(tmp_path: Path) -> None:
    """创建并获取备课会话"""
    app = create_app(
        database_path=tmp_path / "create_get_session.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_session")

        # 创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "备课会话测试班",
                "joinPolicy": "free",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 创建备课会话
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session",
            headers=teacher_headers,
        )
        assert response.status_code == 201
        body = response.json()
        assert body["code"] == "PREPARATION_SESSION_CREATED"
        assert body["data"]["classId"] == class_id
        assert body["data"]["uploadStatus"] == "waiting"
        assert body["data"]["parseStatus"] == "not_started"
        assert body["data"]["currentStep"] == "upload"
        assert body["data"]["originalFilename"] is None
        assert body["data"]["fileFormat"] is None
        assert body["data"]["fileSizeBytes"] is None
        assert body["data"]["parsedContentReference"] is None
        assert body["data"]["highlightsJson"] == "[]"
        assert body["data"]["candidateQuestionsJson"] == "[]"
        assert body["data"]["publicationDraftJson"] == "{}"
        assert body["requestId"] == response.headers["X-Request-Id"]

        # 再次获取备课会话（幂等性）
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session",
            headers=teacher_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == "PREPARATION_SESSION_FETCHED"
        assert body["data"]["classId"] == class_id

        # 使用GET获取备课会话
        response = client.get(
            f"/api/teaching-classes/{class_id}/preparation-session",
            headers=teacher_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == "PREPARATION_SESSION_FETCHED"
        assert body["data"]["classId"] == class_id


def test_update_preparation_session_upload(tmp_path: Path) -> None:
    """更新备课会话上传信息"""
    app = create_app(
        database_path=tmp_path / "update_upload.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_upload")

        # 创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "上传测试班",
                "joinPolicy": "free",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 创建备课会话
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session",
            headers=teacher_headers,
        )
        assert response.status_code == 201

        # 更新上传信息
        upload_data = {
            "originalFilename": "test.pdf",
            "fileFormat": "pdf",
            "fileSizeBytes": 1024,
        }
        response = client.put(
            f"/api/teaching-classes/{class_id}/preparation-session/upload",
            headers=teacher_headers,
            files=multipart_file(upload_data),
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == "PREPARATION_SESSION_FILE_REPLACED"
        assert body["data"]["originalFilename"] == "test.pdf"
        assert body["data"]["fileFormat"] == "pdf"
        assert body["data"]["fileSizeBytes"] == 1024
        assert body["data"]["uploadStatus"] == "uploaded"
        assert body["data"]["parseStatus"] == "not_started"
        assert body["data"]["currentStep"] == "upload"
        assert body["data"]["parsedContentReference"] is None
        assert body["data"]["highlightsJson"] == "[]"
        assert body["data"]["candidateQuestionsJson"] == "[]"
        assert body["data"]["publicationDraftJson"] == "{}"


def test_update_upload_with_invalid_format(tmp_path: Path) -> None:
    """使用不支持的文件格式更新上传信息"""
    app = create_app(
        database_path=tmp_path / "invalid_format.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_invalid")

        # 创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "无效格式测试班",
                "joinPolicy": "free",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 创建备课会话
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session",
            headers=teacher_headers,
        )
        assert response.status_code == 201

        # 尝试使用不支持的格式
        upload_data = {
            "originalFilename": "test.txt",
            "fileFormat": "txt",  # 不支持
            "fileSizeBytes": 1024,
        }
        response = client.put(
            f"/api/teaching-classes/{class_id}/preparation-session/upload",
            headers=teacher_headers,
            files=multipart_file(upload_data),
        )
        assert response.status_code == 422
        assert response.json()["code"] == "UNSUPPORTED_UPLOAD_FORMAT"


def test_update_upload_with_too_large_file(tmp_path: Path) -> None:
    """使用过大的文件更新上传信息"""
    app = create_app(
        database_path=tmp_path / "large_file.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_large")

        # 创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "大文件测试班",
                "joinPolicy": "free",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 创建备课会话
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session",
            headers=teacher_headers,
        )
        assert response.status_code == 201

        # 尝试使用过大的文件
        upload_data = {
            "originalFilename": "large.pdf",
            "fileFormat": "pdf",
            "fileSizeBytes": 20971521,  # 超过20MB
        }
        response = client.put(
            f"/api/teaching-classes/{class_id}/preparation-session/upload",
            headers=teacher_headers,
            files=multipart_file(upload_data),
        )
        assert response.status_code == 422
        assert response.json()["code"] == "UPLOAD_FILE_TOO_LARGE"


def test_get_nonexistent_preparation_session(tmp_path: Path) -> None:
    """获取不存在的备课会话"""
    app = create_app(
        database_path=tmp_path / "nonexistent_session.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_nonexistent")

        # 创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "不存在会话测试班",
                "joinPolicy": "free",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 尝试获取不存在的备课会话
        response = client.get(
            f"/api/teaching-classes/{class_id}/preparation-session",
            headers=teacher_headers,
        )
        assert response.status_code == 404
        assert response.json()["code"] == "PREPARATION_SESSION_NOT_FOUND"


def test_update_nonexistent_preparation_session(tmp_path: Path) -> None:
    """更新不存在的备课会话"""
    app = create_app(
        database_path=tmp_path / "update_nonexistent.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_update_nonexistent")

        # 创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "更新不存在测试班",
                "joinPolicy": "free",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 尝试更新不存在的备课会话
        upload_data = {
            "originalFilename": "test.pdf",
            "fileFormat": "pdf",
            "fileSizeBytes": 1024,
        }
        response = client.put(
            f"/api/teaching-classes/{class_id}/preparation-session/upload",
            headers=teacher_headers,
            files=multipart_file(upload_data),
        )
        assert response.status_code == 404
        assert response.json()["code"] == "PREPARATION_SESSION_NOT_FOUND"


def test_teacher_isolation_preparation_session(tmp_path: Path) -> None:
    """教师A不能访问教师B的备课会话"""
    app = create_app(
        database_path=tmp_path / "teacher_isolation_session.db",
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

        # 教师A创建备课会话
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session",
            headers=teacher_a_headers,
        )
        assert response.status_code == 201

        # 教师B尝试获取教师A的备课会话
        response = client.get(
            f"/api/teaching-classes/{class_id}/preparation-session",
            headers=teacher_b_headers,
        )
        assert response.status_code == 404
        assert response.json()["code"] == "RESOURCE_NOT_FOUND"
        # 教师B尝试更新教师A的备课会话
        upload_data = {
            "originalFilename": "test.pdf",
            "fileFormat": "pdf",
            "fileSizeBytes": 1024,
        }
        response = client.put(
            f"/api/teaching-classes/{class_id}/preparation-session/upload",
            headers=teacher_b_headers,
            files=multipart_file(upload_data),
        )
        assert response.status_code == 404
        assert response.json()["code"] == "RESOURCE_NOT_FOUND"
def test_learner_forbidden_preparation_session(tmp_path: Path) -> None:
    """学习者无权访问备课会话"""
    app = create_app(
        database_path=tmp_path / "learner_forbidden_session.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher")
        learner_headers = register_user(client, "learner", "learner")

        # 教师创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "学习者禁止测试班",
                "joinPolicy": "free",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 教师创建备课会话
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session",
            headers=teacher_headers,
        )
        assert response.status_code == 201

        # 学习者尝试创建备课会话
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session",
            headers=learner_headers,
        )
        assert response.status_code == 403
        assert response.json()["code"] == "AUTH_ROLE_FORBIDDEN"

        # 学习者尝试获取备课会话
        response = client.get(
            f"/api/teaching-classes/{class_id}/preparation-session",
            headers=learner_headers,
        )
        assert response.status_code == 403
        assert response.json()["code"] == "AUTH_ROLE_FORBIDDEN"

        # 学习者尝试更新备课会话
        upload_data = {
            "originalFilename": "test.pdf",
            "fileFormat": "pdf",
            "fileSizeBytes": 1024,
        }
        response = client.put(
            f"/api/teaching-classes/{class_id}/preparation-session/upload",
            headers=learner_headers,
            files=multipart_file(upload_data),
        )
        assert response.status_code == 403
def test_file_signature_validation(tmp_path):
    """验证文件签名校验"""
    app = create_app(
        database_path=tmp_path / "signature_validation.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_signature")

        # 创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "签名验证测试班",
                "joinPolicy": "free",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 创建备课会话
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session",
            headers=teacher_headers,
        )
        assert response.status_code == 201

        # 测试无效的PDF签名
        response = client.put(
            f"/api/teaching-classes/{class_id}/preparation-session/upload",
            headers=teacher_headers,
            files={"file": ("test.pdf", b"INVALID_PDF_CONTENT")},
        )
        assert response.status_code == 422
        assert response.json()["code"] == "UPLOAD_FILE_SIGNATURE_INVALID"

        # 测试无效的DOCX签名
        response = client.put(
            f"/api/teaching-classes/{class_id}/preparation-session/upload",
            headers=teacher_headers,
            files={"file": ("test.docx", b"INVALID_DOCX_CONTENT")},
        )
        assert response.status_code == 422
        assert response.json()["code"] == "UPLOAD_FILE_SIGNATURE_INVALID"

        # 测试有效的PDF签名
        response = client.put(
            f"/api/teaching-classes/{class_id}/preparation-session/upload",
            headers=teacher_headers,
            files={"file": ("test.pdf", b"%PDF-1.4\ntest content")},
        )
        assert response.status_code == 200

        # 测试有效的DOCX签名
        response = client.put(
            f"/api/teaching-classes/{class_id}/preparation-session/upload",
            headers=teacher_headers,
            files={"file": ("test.docx", b"PK\x03\x04\ntest content")},
        )
        assert response.status_code == 200

        # 测试有效的Markdown
        response = client.put(
            f"/api/teaching-classes/{class_id}/preparation-session/upload",
            headers=teacher_headers,
            files={"file": ("test.md", b"# Markdown content\n\nThis is a test")},
        )
        assert response.status_code == 200


def test_preparation_session_parsing_success(tmp_path):
    """测试解析成功场景"""
    parsing = StubCourseContentParsing([
        ParsingResult(
            status=ParsingStatus.COMPLETED,
            paragraphs=[
                ParsedParagraph(order=1, block_type="text", content="第一段内容"),
                ParsedParagraph(order=2, block_type="heading", content="标题"),
                ParsedParagraph(order=3, block_type="text", content="第二段内容"),
            ],
        ),
    ])
    app = create_app(
        database_path=tmp_path / "parsing_success.db",
        jwt_secret="test-secret-with-enough-length",
        course_content_parsing=parsing,
        parsing_executor=lambda task: task(),
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_parsing")

        # 创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "解析成功测试班",
                "joinPolicy": "free",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 创建备课会话
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session",
            headers=teacher_headers,
        )
        assert response.status_code == 201

        # 上传文件
        response = client.put(
            f"/api/teaching-classes/{class_id}/preparation-session/upload",
            headers=teacher_headers,
            files={"file": ("test.pdf", b"%PDF-1.4\ntest content")},
        )
        assert response.status_code == 200

        # 开始解析
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/parse",
            headers=teacher_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["parseStatus"] == "parsing"

        # 获取解析结果
        response = client.get(
            f"/api/teaching-classes/{class_id}/preparation-session/parsed-paragraphs",
            headers=teacher_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["session"]["parseStatus"] == "completed"
        assert len(data["paragraphs"]) == 3
        assert data["paragraphs"][0]["ordinal"] == 1
        assert data["paragraphs"][0]["content"] == "第一段内容"


def test_preparation_session_parsing_timeout(tmp_path):
    """测试解析超时场景"""
    parsing = StubCourseContentParsing([
        ParsingResult(
            status=ParsingStatus.TIMED_OUT,
            paragraphs=[],
        ),
    ])
    app = create_app(
        database_path=tmp_path / "parsing_timeout.db",
        jwt_secret="test-secret-with-enough-length",
        course_content_parsing=parsing,
        parsing_executor=lambda task: task(),
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_timeout")

        # 创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "解析超时测试班",
                "joinPolicy": "free",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 创建备课会话
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session",
            headers=teacher_headers,
        )
        assert response.status_code == 201

        # 上传文件
        response = client.put(
            f"/api/teaching-classes/{class_id}/preparation-session/upload",
            headers=teacher_headers,
            files={"file": ("test.pdf", b"%PDF-1.4\ntest content")},
        )
        assert response.status_code == 200

        # 开始解析
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/parse",
            headers=teacher_headers,
        )
        assert response.status_code == 200

        # 获取解析结果
        response = client.get(
            f"/api/teaching-classes/{class_id}/preparation-session/parsed-paragraphs",
            headers=teacher_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["session"]["parseStatus"] == "timed_out"
        assert data["session"]["parseErrorCode"] == "PARSING_TIMED_OUT"


def test_preparation_session_parsing_failed(tmp_path):
    """测试解析失败场景"""
    parsing = StubCourseContentParsing([
        ParsingResult(
            status=ParsingStatus.FAILED,
            paragraphs=[],
        ),
    ])
    app = create_app(
        database_path=tmp_path / "parsing_failed.db",
        jwt_secret="test-secret-with-enough-length",
        course_content_parsing=parsing,
        parsing_executor=lambda task: task(),
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_failed")

        # 创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "解析失败测试班",
                "joinPolicy": "free",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 创建备课会话
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session",
            headers=teacher_headers,
        )
        assert response.status_code == 201

        # 上传文件
        response = client.put(
            f"/api/teaching-classes/{class_id}/preparation-session/upload",
            headers=teacher_headers,
            files={"file": ("test.pdf", b"%PDF-1.4\ntest content")},
        )
        assert response.status_code == 200

        # 开始解析
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/parse",
            headers=teacher_headers,
        )
        assert response.status_code == 200

        # 获取解析结果
        response = client.get(
            f"/api/teaching-classes/{class_id}/preparation-session/parsed-paragraphs",
            headers=teacher_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["session"]["parseStatus"] == "failed"
        assert data["session"]["parseErrorCode"] == "PARSING_FAILED"


def test_preparation_session_logs_failed_result(tmp_path, caplog):
    """解析器返回失败结果时，后台应记录失败原因。"""
    parsing = StubCourseContentParsing([
        ParsingResult(
            status=ParsingStatus.FAILED,
            paragraphs=[],
            error_message="解析器返回失败",
        ),
    ])
    app = create_app(
        database_path=tmp_path / "parsing_failed_log.db",
        jwt_secret="test-secret-with-enough-length",
        course_content_parsing=parsing,
        parsing_executor=lambda task: task(),
    )

    with caplog.at_level(logging.WARNING, logger="course_agent.preparation_sessions"):
        with TestClient(app) as client:
            teacher_headers = register_user(client, "teacher_failed_log")
            class_id = client.post(
                "/api/teaching-classes",
                headers=teacher_headers,
                json={"name": "解析日志测试班", "joinPolicy": "free"},
            ).json()["data"]["id"]
            client.post(
                f"/api/teaching-classes/{class_id}/preparation-session",
                headers=teacher_headers,
            )
            uploaded = client.put(
                f"/api/teaching-classes/{class_id}/preparation-session/upload",
                headers=teacher_headers,
                files={"file": ("test.pdf", b"%PDF-1.4\ntest content")},
            )
            assert uploaded.status_code == 200
            started = client.post(
                f"/api/teaching-classes/{class_id}/preparation-session/parse",
                headers=teacher_headers,
            )
            assert started.status_code == 200

    assert "preparation_session_parse_failed" in caplog.text
    assert "PARSING_FAILED" in caplog.text
    assert "解析器返回失败" in caplog.text


def test_preparation_session_retry_after_failure(tmp_path):
    """测试失败后重试"""
    parse_results = [
        ParsingResult(status=ParsingStatus.FAILED, paragraphs=[]),  # 第一次失败
        ParsingResult(
            status=ParsingStatus.COMPLETED,
            paragraphs=[
                ParsedParagraph(order=1, block_type="text", content="重试成功内容"),
            ],
        ),  # 第二次成功
    ]

    app = create_app(
        database_path=tmp_path / "retry_test.db",
        jwt_secret="test-secret-with-enough-length",
        course_content_parsing=StubCourseContentParsing(parse_results),
        parsing_executor=lambda task: task(),
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_retry")

        # 创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "重试测试班",
                "joinPolicy": "free",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 创建备课会话
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session",
            headers=teacher_headers,
        )
        assert response.status_code == 201

        # 上传文件
        response = client.put(
            f"/api/teaching-classes/{class_id}/preparation-session/upload",
            headers=teacher_headers,
            files={"file": ("test.pdf", b"%PDF-1.4\ntest content")},
        )
        assert response.status_code == 200

        # 第一次解析（失败）
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/parse",
            headers=teacher_headers,
        )
        assert response.status_code == 200

        # 检查失败状态
        response = client.get(
            f"/api/teaching-classes/{class_id}/preparation-session",
            headers=teacher_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["parseStatus"] == "failed"

        # 重试解析
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/parse",
            headers=teacher_headers,
        )
        assert response.status_code == 200

        # 检查成功状态
        response = client.get(
            f"/api/teaching-classes/{class_id}/preparation-session/parsed-paragraphs",
            headers=teacher_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["session"]["parseStatus"] == "completed"
        assert len(data["paragraphs"]) == 1


def test_highlights_functionality(tmp_path):
    """测试教学重点功能：新增、取消、冲突、文件重选清空和跨教师访问"""
    parsing = StubCourseContentParsing([
        ParsingResult(
            status=ParsingStatus.COMPLETED,
            paragraphs=[
                ParsedParagraph(order=1, block_type="text", content="这是第一段内容，用于测试教学重点功能。"),
                ParsedParagraph(order=2, block_type="heading", content="测试标题"),
                ParsedParagraph(order=3, block_type="text", content="这是第二段内容，也用于测试。"),
            ],
        ),
    ])
    app = create_app(
        database_path=tmp_path / "highlights_test.db",
        jwt_secret="test-secret-with-enough-length",
        course_content_parsing=parsing,
        parsing_executor=lambda task: task(),
    )

    with TestClient(app) as client:
        teacher_a_headers = register_user(client, "teacher_a")
        teacher_b_headers = register_user(client, "teacher_b")

        # 教师A创建教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_a_headers,
            json={
                "name": "教学重点测试班",
                "joinPolicy": "free",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 创建备课会话
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session",
            headers=teacher_a_headers,
        )
        assert response.status_code == 201

        # 上传文件并解析
        response = client.put(
            f"/api/teaching-classes/{class_id}/preparation-session/upload",
            headers=teacher_a_headers,
            files={"file": ("test.pdf", b"%PDF-1.4\ntest content")},
        )
        assert response.status_code == 200

        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/parse",
            headers=teacher_a_headers,
        )
        assert response.status_code == 200

        # 测试1: 新增教学重点
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/highlights",
            headers=teacher_a_headers,
            json={
                "paragraphOrdinal": 1,
                "startOffset": 0,
                "endOffset": 4,  # "这是"
            },
        )
        assert response.status_code == 201
        highlight_data = response.json()["data"]
        assert highlight_data["paragraphOrdinal"] == 1
        assert highlight_data["startOffset"] == 0
        assert highlight_data["endOffset"] == 4
        highlight_id = highlight_data["id"]

        # 测试2: 获取带教学重点的段落
        response = client.get(
            f"/api/teaching-classes/{class_id}/preparation-session/parsed-paragraphs-with-highlights",
            headers=teacher_a_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["totalHighlights"] == 1
        assert len(data["paragraphs"]) == 3

        # 检查第一个段落有教学重点
        first_paragraph = data["paragraphs"][0]
        assert first_paragraph["hasHighlights"] == True
        assert len(first_paragraph["highlights"]) == 1
        assert first_paragraph["highlights"][0]["id"] == highlight_id

        # 测试3: 新增冲突的教学重点（重叠）
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/highlights",
            headers=teacher_a_headers,
            json={
                "paragraphOrdinal": 1,
                "startOffset": 2,
                "endOffset": 6,  # 与现有重点重叠
            },
        )
        assert response.status_code == 409
        assert response.json()["code"] == "HIGHLIGHT_OVERLAP"

        # 测试4: 新增重复的教学重点
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/highlights",
            headers=teacher_a_headers,
            json={
                "paragraphOrdinal": 1,
                "startOffset": 0,
                "endOffset": 4,  # 与现有重点完全相同
            },
        )
        assert response.status_code == 409
        assert response.json()["code"] == "HIGHLIGHT_DUPLICATE"

        # 测试5: 新增越界的教学重点
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/highlights",
            headers=teacher_a_headers,
            json={
                "paragraphOrdinal": 1,
                "startOffset": 100,
                "endOffset": 105,  # 超出段落长度
            },
        )
        assert response.status_code == 400
        assert response.json()["code"] == "INVALID_OFFSET_RANGE"

        # 测试6: 取消教学重点
        response = client.request(
            "DELETE",
            f"/api/teaching-classes/{class_id}/preparation-session/highlights",
            headers=teacher_a_headers,
            json={
                "highlightId": highlight_id,
            },
        )
        assert response.status_code == 200

        # 验证教学重点已被取消
        response = client.get(
            f"/api/teaching-classes/{class_id}/preparation-session/parsed-paragraphs-with-highlights",
            headers=teacher_a_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["totalHighlights"] == 0
        assert data["paragraphs"][0]["hasHighlights"] == False
        assert len(data["paragraphs"][0]["highlights"]) == 0

        # 测试7: 取消不存在的教学重点
        response = client.request(
            "DELETE",
            f"/api/teaching-classes/{class_id}/preparation-session/highlights",
            headers=teacher_a_headers,
            json={
                "highlightId": "nonexistent-id",
            },
        )
        assert response.status_code == 404
        assert response.json()["code"] == "HIGHLIGHT_NOT_FOUND"

        # 测试8: 文件重选清空教学重点
        # 先添加一个教学重点
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/highlights",
            headers=teacher_a_headers,
            json={
                "paragraphOrdinal": 1,
                "startOffset": 5,
                "endOffset": 8,
            },
        )
        assert response.status_code == 201

        # 替换文件
        response = client.put(
            f"/api/teaching-classes/{class_id}/preparation-session/upload",
            headers=teacher_a_headers,
            files={"file": ("new.pdf", b"%PDF-1.4\nnew content")},
        )
        assert response.status_code == 200

        # 验证教学重点已被清空
        response = client.get(
            f"/api/teaching-classes/{class_id}/preparation-session/parsed-paragraphs-with-highlights",
            headers=teacher_a_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["totalHighlights"] == 0
        assert data["session"]["parseStatus"] == "not_started"

        # 测试9: 跨教师访问
        # 教师B尝试访问教师A的教学重点
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/highlights",
            headers=teacher_b_headers,
            json={
                "paragraphOrdinal": 1,
                "startOffset": 0,
                "endOffset": 4,
            },
        )
        assert response.status_code == 404
        assert response.json()["code"] == "RESOURCE_NOT_FOUND"

        response = client.request(
            "DELETE",
            f"/api/teaching-classes/{class_id}/preparation-session/highlights",
            headers=teacher_b_headers,
            json={
                "highlightId": "any-id",
            },
        )
        assert response.status_code == 404
        assert response.json()["code"] == "RESOURCE_NOT_FOUND"

def test_questions_functionality(tmp_path):
    """测试题目功能：手工题、候选题确认、删除、非法结构、解锁条件和跨教师权限"""
    app, database = build_app(
        database_path=tmp_path / "questions_test.db",
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
                "name": "题目功能测试班",
                "joinPolicy": "free",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 创建备课会话
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session",
            headers=teacher_a_headers,
        )
        assert response.status_code == 201

        # 测试1: 获取空题目列表
        response = client.get(
            f"/api/teaching-classes/{class_id}/preparation-session/questions",
            headers=teacher_a_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["items"]) == 0
        assert data["isPublishUnlocked"] == False
        assert data["canGenerateFromHighlights"] == False

        # 测试2: 创建手工题（单选题）
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/questions",
            headers=teacher_a_headers,
            json={
                "type": "single_choice",
                "stem": "什么是Python？",
                "options": ["编程语言", "动物", "食物", "城市"],
                "answers": [0],
                "knowledgePoints": ["编程", "Python"],
                "highlightSourceIds": [],
                "hint": "考虑Python的用途",
                "explanation": "Python是一种高级编程语言",
            },
        )
        assert response.status_code == 201
        question_data = response.json()["data"]
        assert question_data["source"] == "manual"
        assert question_data["reviewStatus"] == "confirmed"
        assert question_data["type"] == "single_choice"
        assert question_data["stem"] == "什么是Python？"
        assert question_data["answers"] == [0]
        manual_question_id = question_data["id"]

        # 测试3: 创建手工题（多选题）
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/questions",
            headers=teacher_a_headers,
            json={
                "type": "multiple_choice",
                "stem": "以下哪些是编程语言？",
                "options": ["Python", "Java", "大象", "C++"],
                "answers": [0, 1, 3],
                "knowledgePoints": ["编程", "语言"],
                "highlightSourceIds": [],
                "hint": "排除非编程相关选项",
                "explanation": "Python、Java、C++都是编程语言",
            },
        )
        assert response.status_code == 201

        # 测试4: 获取题目列表（应有2题）
        response = client.get(
            f"/api/teaching-classes/{class_id}/preparation-session/questions",
            headers=teacher_a_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["items"]) == 2
        assert data["isPublishUnlocked"] == True  # 有手工题，发布解锁
        assert data["canGenerateFromHighlights"] == False

        # 测试5: 更新手工题
        response = client.put(
            f"/api/teaching-classes/{class_id}/preparation-session/questions/{manual_question_id}",
            headers=teacher_a_headers,
            json={
                "type": "single_choice",
                "stem": "Python是什么类型的语言？",
                "options": ["高级编程语言", "低级语言", "标记语言", "查询语言"],
                "answers": [0],
                "knowledgePoints": ["编程", "Python", "语言类型"],
                "highlightSourceIds": [],
                "hint": "考虑Python的特点",
                "explanation": "Python是一种高级编程语言",
            },
        )
        assert response.status_code == 200
        updated_data = response.json()["data"]
        assert updated_data["stem"] == "Python是什么类型的语言？"
        assert updated_data["knowledgePoints"] == ["编程", "Python", "语言类型"]

        # 测试6: 创建候选题（模拟生成的题目）
        candidate_question = {
            "id": str(uuid.uuid4()),
            "source": "candidate",
            "review_status": "candidate",
            "type": "single_choice",
            "stem": "Python中如何定义函数？",
            "options": ["def", "function", "define", "func"],
            "answers": [0],
            "knowledge_points": ["Python", "函数"],
            "highlight_source_ids": [],
            "hint": "查看Python语法",
            "explanation": "Python使用def关键字定义函数",
            "created_at": int(time.time()),
            "updated_at": int(time.time()),
        }

        # 通过 v4 题目关系表添加候选题
        with database.connect() as connection:
            session = connection.execute(
                "SELECT id FROM preparation_sessions WHERE class_id=?",
                (class_id,)
            ).fetchone()
            if session:
                connection.execute(
                    """
                    INSERT INTO preparation_questions(
                        id, session_id, source, review_status, question_type, stem,
                        options_json, correct_answers_json, knowledge_points_json,
                        highlight_source_ids_json, hint, explanation, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        candidate_question["id"], session["id"], candidate_question["source"],
                        candidate_question["review_status"], candidate_question["type"], candidate_question["stem"],
                        json.dumps(candidate_question["options"]), json.dumps(candidate_question["answers"]),
                        json.dumps(candidate_question["knowledge_points"]), json.dumps(candidate_question["highlight_source_ids"]),
                        candidate_question["hint"], candidate_question["explanation"],
                        candidate_question["created_at"], candidate_question["updated_at"],
                    ),
                )

        # 测试7: 获取题目列表（应有3题，发布未解锁）
        response = client.get(
            f"/api/teaching-classes/{class_id}/preparation-session/questions",
            headers=teacher_a_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["items"]) == 3
        assert data["isPublishUnlocked"] == False  # 有候选题未确认，发布未解锁

        # 测试8: 确认候选题
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/questions/confirm",
            headers=teacher_a_headers,
            json={
                "questionId": candidate_question["id"],
            },
        )
        assert response.status_code == 200
        confirmed_data = response.json()["data"]
        assert confirmed_data["reviewStatus"] == "confirmed"

        # 测试9: 获取题目列表（发布已解锁）
        response = client.get(
            f"/api/teaching-classes/{class_id}/preparation-session/questions",
            headers=teacher_a_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["isPublishUnlocked"] == True  # 候选题已确认，发布解锁

        # 测试10: 删除题目
        response = client.request(
            "DELETE",
            f"/api/teaching-classes/{class_id}/preparation-session/questions",
            headers=teacher_a_headers,
            json={
                "questionId": manual_question_id,
            },
        )
        assert response.status_code == 200

        # 验证题目已删除
        response = client.get(
            f"/api/teaching-classes/{class_id}/preparation-session/questions",
            headers=teacher_a_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["items"]) == 2

        # 测试11: 非法题目结构（单选题多个答案）
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/questions",
            headers=teacher_a_headers,
            json={
                "type": "single_choice",
                "stem": "测试题",
                "options": ["A", "B", "C"],
                "answers": [0, 1],  # 单选题不能有多个答案
                "knowledgePoints": ["测试"],
                "highlightSourceIds": [],
                "hint": "",
                "explanation": "",
            },
        )
        assert response.status_code == 422  # Pydantic验证失败

        # 测试12: 跨教师权限
        # 教师B尝试操作教师A的题目
        response = client.get(
            f"/api/teaching-classes/{class_id}/preparation-session/questions",
            headers=teacher_b_headers,
        )
        assert response.status_code == 404

        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/questions",
            headers=teacher_b_headers,
            json={
                "type": "single_choice",
                "stem": "测试题",
                "options": ["A", "B"],
                "answers": [0],
                "knowledgePoints": ["测试"],
                "highlightSourceIds": [],
                "hint": "",
                "explanation": "",
            },
        )
        assert response.status_code == 404

        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/questions/confirm",
            headers=teacher_b_headers,
            json={
                "questionId": candidate_question["id"],
            },
        )
        assert response.status_code == 404

        response = client.request(
            "DELETE",
            f"/api/teaching-classes/{class_id}/preparation-session/questions",
            headers=teacher_b_headers,
            json={
                "questionId": candidate_question["id"],
            },
        )
        assert response.status_code == 404

        # 测试13: 无效的highlight_source_ids验证
        # 先创建教学重点
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/highlights",
            headers=teacher_a_headers,
            json={
                "paragraphOrdinal": 1,
                "startOffset": 0,
                "endOffset": 5,
            },
        )
        assert response.status_code == 400  # 没有段落，会失败

        # 测试14: 验证canGenerateFromHighlights
        # 上传文件并解析以创建段落
        response = client.put(
            f"/api/teaching-classes/{class_id}/preparation-session/upload",
            headers=teacher_a_headers,
            files={"file": ("test.pdf", b"%PDF-1.4\ntest content")},
        )
        assert response.status_code == 200

        # 添加教学重点
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/highlights",
            headers=teacher_a_headers,
            json={
                "paragraphOrdinal": 1,
                "startOffset": 0,
                "endOffset": 4,
            },
        )
        assert response.status_code == 400  # 解析未完成

        # 测试15: 删除不存在的题目
        response = client.request(
            "DELETE",
            f"/api/teaching-classes/{class_id}/preparation-session/questions",
            headers=teacher_a_headers,
            json={
                "questionId": "nonexistent-id",
            },
        )
        assert response.status_code == 404

        # 测试16: 更新不存在的题目
        response = client.put(
            f"/api/teaching-classes/{class_id}/preparation-session/questions/nonexistent-id",
            headers=teacher_a_headers,
            json={
                "type": "single_choice",
                "stem": "测试题",
                "options": ["A", "B"],
                "answers": [0],
                "knowledgePoints": ["测试"],
                "highlightSourceIds": [],
                "hint": "",
                "explanation": "",
            },
        )
        assert response.status_code == 404

        # 测试17: 确认不存在的题目
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/questions/confirm",
            headers=teacher_a_headers,
            json={
                "questionId": "nonexistent-id",
            },
        )
        assert response.status_code == 404

        # 测试18: 确认非候选题（手工题）
        # 创建一个手工题
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/questions",
            headers=teacher_a_headers,
            json={
                "type": "single_choice",
                "stem": "测试手工题",
                "options": ["A", "B"],
                "answers": [0],
                "knowledgePoints": ["测试"],
                "highlightSourceIds": [],
                "hint": "",
                "explanation": "",
            },
        )
        assert response.status_code == 201
        manual_id = response.json()["data"]["id"]

        # 尝试确认手工题（应该失败）
        response = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/questions/confirm",
            headers=teacher_a_headers,
            json={
                "questionId": manual_id,
            },
        )
        assert response.status_code == 400
        assert response.json()["code"] == "INVALID_QUESTION_SOURCE"
