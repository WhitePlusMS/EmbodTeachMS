"""学习者课程内容详情模型测试"""

import pytest
from app.teaching_classes.models import (
    ContentType,
    PublishedContentDetailView,
)


def test_published_content_detail_view_with_highlights():
    """测试已发布内容详情视图包含教学重点"""
    content = PublishedContentDetailView(
        id="test-id",
        class_id="class-1",
        content_type=ContentType.KNOWLEDGE_MODULE.value,
        publication_status="published",
        title="知识模块",
        content="模块内容",
        created_at=1000,
        updated_at=1000,
        highlights_json='[{"id": "h1", "paragraphOrdinal": 1, "startOffset": 0, "endOffset": 4, "createdAt": 1000}]',
        source_preparation_session_id="session-1",
        source_teacher_id="teacher-1",
        source_filename="document.pdf",
    )

    assert content.highlights_json == '[{"id": "h1", "paragraphOrdinal": 1, "startOffset": 0, "endOffset": 4, "createdAt": 1000}]'
    assert content.source_preparation_session_id == "session-1"
    assert content.source_teacher_id == "teacher-1"
    assert content.source_filename == "document.pdf"


def test_published_content_detail_view_without_source_info():
    """测试已发布内容详情视图可以没有来源信息"""
    content = PublishedContentDetailView(
        id="test-id",
        class_id="class-1",
        content_type=ContentType.KNOWLEDGE_MODULE.value,
        publication_status="published",
        title="知识模块",
        content="模块内容",
        created_at=1000,
        updated_at=1000,
        highlights_json="[]",
        source_preparation_session_id=None,
        source_teacher_id=None,
        source_filename=None,
    )

    assert content.highlights_json == "[]"
    assert content.source_preparation_session_id is None
    assert content.source_teacher_id is None
    assert content.source_filename is None


def test_published_content_detail_view_homework_fields():
    """测试作业内容详情包含作业特有字段"""
    content = PublishedContentDetailView(
        id="test-id",
        class_id="class-1",
        content_type=ContentType.HOMEWORK.value,
        publication_status="published",
        title="数学作业",
        content="完成练习题",
        created_at=1000,
        updated_at=1000,
        due_at=2000,
        description="请认真完成作业",
        highlights_json="[]",
        source_preparation_session_id="session-1",
        source_teacher_id="teacher-1",
        source_filename="homework.pdf",
    )

    assert content.content_type == "homework"
    assert content.due_at == 2000
    assert content.description == "请认真完成作业"
    assert content.source_filename == "homework.pdf"


def test_published_content_detail_view_non_homework_fields():
    """测试非作业内容详情作业字段为空"""
    content = PublishedContentDetailView(
        id="test-id",
        class_id="class-1",
        content_type=ContentType.KNOWLEDGE_MODULE.value,
        publication_status="published",
        title="知识模块",
        content="模块内容",
        created_at=1000,
        updated_at=1000,
        due_at=None,
        description=None,
        highlights_json="[]",
        source_preparation_session_id="session-1",
        source_teacher_id="teacher-1",
        source_filename="document.pdf",
    )

    assert content.due_at is None
    assert content.description is None
    assert content.source_filename == "document.pdf"


def test_published_content_detail_view_default_highlights():
    """测试已发布内容详情视图默认教学重点为空数组"""
    content = PublishedContentDetailView(
        id="test-id",
        class_id="class-1",
        content_type=ContentType.KNOWLEDGE_MODULE.value,
        publication_status="published",
        title="知识模块",
        content="模块内容",
        created_at=1000,
        updated_at=1000,
    )

    assert content.highlights_json == "[]"
    assert content.source_preparation_session_id is None
    assert content.source_teacher_id is None
    assert content.source_filename is None
    assert content.due_at is None
    assert content.description is None