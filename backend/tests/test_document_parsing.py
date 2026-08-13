"""文档解析深 module 的边界与注入测试。"""

import asyncio
import logging
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.database import Database
from app.document_parsing import (
    CourseContentParsing,
    DocumentParser,
    MarkdownParser,
    MinerUParser,
    ParsedParagraph,
    ParsingError,
    ParsingLimits,
    ParsingResult,
    ParsingStatus,
)
from app.teaching_classes.models import FileFormat
from app.main import create_app


class RecordingParser(DocumentParser):
    def __init__(self, result: ParsingResult) -> None:
        self.result = result
        self.options: dict[str, int] | None = None

    async def parse(
        self,
        file_path: Path,
        timeout: int = 300,
        max_pages: int = 100,
        max_paragraphs: int = 1000,
        max_output_size: int = 10 * 1024 * 1024,
    ) -> ParsingResult:
        self.options = {
            "timeout": timeout,
            "max_pages": max_pages,
            "max_paragraphs": max_paragraphs,
            "max_output_size": max_output_size,
        }
        return self.result


def test_database_context_closes_connection(tmp_path: Path) -> None:
    database = Database(tmp_path / "connection.db")
    database.initialize()
    with database.connect() as connection:
        assert connection.execute("SELECT 1").fetchone()[0] == 1
    with pytest.raises(sqlite3.ProgrammingError):
        connection.execute("SELECT 1")


def test_course_content_parsing_uses_injected_parser_executor_and_limits(tmp_path: Path) -> None:
    document = tmp_path / "course.md"
    document.write_text("# 标题", encoding="utf-8")
    expected = ParsingResult(
        status=ParsingStatus.COMPLETED,
        paragraphs=[ParsedParagraph(content="标题", order=0, block_type="heading")],
    )
    parser = RecordingParser(expected)
    executor_calls = 0

    def execute(awaitable) -> ParsingResult:
        nonlocal executor_calls
        executor_calls += 1
        return asyncio.run(awaitable)

    parsing = CourseContentParsing(
        markdown_parser_factory=lambda: parser,
        async_executor=execute,
        limits=ParsingLimits(
            timeout=12,
            max_pages=34,
            max_paragraphs=56,
            max_output_size=789,
        ),
    )

    assert parsing.parse(document, FileFormat.MARKDOWN) is expected
    assert executor_calls == 1
    assert parser.options == {
        "timeout": 12,
        "max_pages": 34,
        "max_paragraphs": 56,
        "max_output_size": 789,
    }


def test_course_content_parsing_rejects_declared_format_mismatch(tmp_path: Path) -> None:
    document = tmp_path / "course.md"
    document.write_text("正文", encoding="utf-8")
    parsing = CourseContentParsing(limits=ParsingLimits())

    with pytest.raises(ParsingError) as captured:
        parsing.parse(document, FileFormat.PDF)

    assert captured.value.code == "FILE_FORMAT_MISMATCH"


class FailingCourseParser(CourseContentParsing):
    def __init__(self) -> None:
        pass

    def parse(self, file_path: Path, file_format: FileFormat) -> ParsingResult:
        raise ParsingError(code="MINERU_CONFIG_MISSING", message="测试错误")


def test_preparation_session_preserves_parser_error_code(tmp_path: Path, caplog) -> None:
    app = create_app(
        database_path=tmp_path / "parser-error.db",
        jwt_secret="test-secret-with-enough-length",
        course_content_parsing=FailingCourseParser(),
        parsing_executor=lambda task: task(),
    )
    with caplog.at_level(logging.WARNING, logger="course_agent.preparation_sessions"):
        with TestClient(app) as client:
            registered = client.post(
                "/api/auth/register",
                json={
                    "username": "parser_error_teacher",
                    "password": "StrongPass123!",
                    "displayName": "解析教师",
                    "role": "teacher",
                },
            )
            headers = {
                "Authorization": f"Bearer {registered.json()['data']['accessToken']}"
            }
            class_id = client.post(
                "/api/teaching-classes",
                headers=headers,
                json={"name": "解析错误码班", "joinPolicy": "free"},
            ).json()["data"]["id"]
            client.post(
                f"/api/teaching-classes/{class_id}/preparation-session",
                headers=headers,
            )
            uploaded = client.put(
                f"/api/teaching-classes/{class_id}/preparation-session/upload",
                headers=headers,
                files={"file": ("course.md", b"# course")},
            )
            assert uploaded.status_code == 200
            started = client.post(
                f"/api/teaching-classes/{class_id}/preparation-session/parse",
                headers=headers,
            )
            assert started.status_code == 200
            parsed = client.get(
                f"/api/teaching-classes/{class_id}/preparation-session/parsed-paragraphs",
                headers=headers,
            )
            assert parsed.json()["data"]["session"]["parseStatus"] == "failed"
            assert (
                parsed.json()["data"]["session"]["parseErrorCode"]
                == "MINERU_CONFIG_MISSING"
            )

    assert "error_code=MINERU_CONFIG_MISSING" in caplog.text
    assert "error_message=测试错误" in caplog.text


def test_markdown_parser_extracts_headings_lists_and_paragraphs(tmp_path: Path) -> None:
    document = tmp_path / "course.md"
    document.write_text(
        "# 标题\n"
        "\n"
        "第一段 `代码` 内容\n"
        "\n"
        "- 列表项一\n"
        "\n"
        "```python\n"
        "print('不应出现')\n"
        "```\n"
        "\n"
        "第二段 [链接文字](https://example.com) 结尾\n",
        encoding="utf-8",
    )

    result = asyncio.run(MarkdownParser().parse(document))

    assert result.status is ParsingStatus.COMPLETED
    assert [(item.order, item.block_type, item.content) for item in result.paragraphs] == [
        (0, "heading", "标题"),
        (1, "paragraph", "第一段 代码 内容"),
        (2, "list", "列表项一"),
        (3, "paragraph", "第二段 链接文字 结尾"),
    ]


def test_markdown_parser_normalize_text_strips_markup() -> None:
    parser = MarkdownParser()

    assert (
        parser._normalize_text("`代码` <b>加粗</b> [链接](https://example.com)  多余   空白")
        == "代码 加粗 链接 多余 空白"
    )


def test_markdown_parser_respects_output_size_limit(tmp_path: Path) -> None:
    document = tmp_path / "course.md"
    document.write_text("甲" * 10 + "\n\n" + "乙" * 10, encoding="utf-8")

    result = asyncio.run(MarkdownParser().parse(document, max_output_size=30))

    assert result.status is ParsingStatus.COMPLETED
    assert [item.content for item in result.paragraphs] == ["甲" * 10]


def test_markdown_parser_respects_max_paragraphs_limit(tmp_path: Path) -> None:
    document = tmp_path / "course.md"
    document.write_text("一\n\n二\n\n三", encoding="utf-8")

    result = asyncio.run(MarkdownParser().parse(document, max_paragraphs=2))

    assert result.status is ParsingStatus.COMPLETED
    assert [item.content for item in result.paragraphs] == ["一", "二"]


def test_markdown_parser_reports_decode_error(tmp_path: Path) -> None:
    document = tmp_path / "course.md"
    document.write_bytes(b"\xff\xfe\x00invalid")

    with pytest.raises(ParsingError) as captured:
        asyncio.run(MarkdownParser().parse(document))

    assert captured.value.code == "MARKDOWN_DECODE_ERROR"


def test_mineru_parser_requires_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MINERU_BASE_URL", raising=False)

    with pytest.raises(ParsingError) as captured:
        MinerUParser()

    assert captured.value.code == "MINERU_CONFIG_MISSING"


def test_mineru_parser_strips_trailing_slash_from_base_url() -> None:
    parser = MinerUParser(base_url="http://mineru.internal:8080/")

    assert parser.base_url == "http://mineru.internal:8080"
