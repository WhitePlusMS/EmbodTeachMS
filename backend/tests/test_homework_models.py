"""作业模型测试"""

import pytest
from app.teaching_classes.models import (
    ContentType,
    PublishedContentView,
    PublishHomeworkRequest,
)


def test_content_type_enum():
    """测试内容类型枚举包含作业类型"""
    assert hasattr(ContentType, "HOMEWORK")
    assert ContentType.HOMEWORK.value == "homework"


def test_published_content_view_with_homework_fields():
    """测试已发布内容视图支持作业特有字段"""
    content = PublishedContentView(
        id="test-id",
        class_id="class-1",
        content_type=ContentType.HOMEWORK.value,
        publication_status="published",
        title="作业标题",
        content="作业内容",
        created_at=1000,
        updated_at=1000,
        due_at=2000,
        description="作业描述",
    )

    assert content.due_at == 2000
    assert content.description == "作业描述"
    assert content.content_type == "homework"


def test_published_content_view_without_homework_fields():
    """测试已发布内容视图对非作业内容保持兼容"""
    content = PublishedContentView(
        id="test-id",
        class_id="class-1",
        content_type=ContentType.KNOWLEDGE_MODULE.value,
        publication_status="published",
        title="知识模块",
        content="模块内容",
        created_at=1000,
        updated_at=1000,
    )

    assert content.due_at is None
    assert content.description is None
    assert content.content_type == "knowledge_module"


def test_publish_homework_request_validation():
    """测试发布作业请求验证"""
    # 正常请求
    request = PublishHomeworkRequest(
        title="作业标题",
        due_at=2000,
        description="作业描述",
    )

    assert request.title == "作业标题"
    assert request.due_at == 2000
    assert request.description == "作业描述"


def test_publish_homework_request_title_validation():
    """测试发布作业请求标题验证"""
    # 空标题应该失败
    with pytest.raises(ValueError, match="标题不能为空或纯空白"):
        PublishHomeworkRequest(title="", due_at=2000)

    # 纯空白标题应该失败
    with pytest.raises(ValueError, match="标题不能为空或纯空白"):
        PublishHomeworkRequest(title="   ", due_at=2000)


def test_publish_homework_request_due_at_validation():
    """测试发布作业请求截止时间验证"""
    # 无效截止时间应该失败
    with pytest.raises(ValueError, match="截止时间必须为正数"):
        PublishHomeworkRequest(title="作业标题", due_at=0)

    with pytest.raises(ValueError, match="截止时间必须为正数"):
        PublishHomeworkRequest(title="作业标题", due_at=-1000)


def test_publish_homework_request_description_optional():
    """测试发布作业请求描述可选"""
    # 描述可选
    request = PublishHomeworkRequest(
        title="作业标题",
        due_at=2000,
    )

    assert request.description == ""

    # 空描述
    request = PublishHomeworkRequest(
        title="作业标题",
        due_at=2000,
        description="",
    )

    assert request.description == ""