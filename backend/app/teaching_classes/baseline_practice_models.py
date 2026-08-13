from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel
from app.teaching_classes.mastery_models import ResultType


class BaselinePracticeStatus(StrEnum):
    """基准练习状态"""
    INITIAL = "initial"  # 初始状态，未开始
    PROMPT_SHOWN = "prompt_shown"  # 提示已显示（第一次错误后）
    COMPLETED = "completed"  # 已结束（首次答对，或第二次作答后无论对错）
    ABANDONED = "abandoned"  # 主动放弃


class BaselinePracticeSubmitRequest(BaseModel):
    """基准练习 HTTP 提交请求；学习者身份由当前会话提供。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    selected_answers: list[int] = Field(default_factory=list)

    @field_validator("selected_answers")
    @classmethod
    def validate_selected_answers(cls, selected_answers: list[int]) -> list[int]:
        if any(answer < 0 for answer in selected_answers):
            raise ValueError("答案索引不能为负数")
        return selected_answers


class BaselinePracticeResult(BaseModel):
    """基准练习提交结果"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    is_correct: bool  # 是否正确
    status: BaselinePracticeStatus  # 当前状态
    correct_answers: list[int] = Field(default_factory=list)  # 正确答案索引
    explanation: str = ""  # 解析
    hint: str = ""  # 提示（仅在PROMPT_SHOWN状态时提供）
    can_submit_again: bool = True  # 是否可以再次提交


class BaselinePracticeDetail(BaseModel):
    """基准练习详情"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    learner_id: str
    class_id: str
    content_id: str
    status: BaselinePracticeStatus
    first_attempt_answers: list[int] = Field(default_factory=list)  # 第一次作答答案
    second_attempt_answers: list[int] = Field(default_factory=list)  # 第二次作答答案
    final_answers: list[int] = Field(default_factory=list)  # 最终答案
    is_correct: Optional[bool] = None  # 是否正确（仅终态时有效）
    correct_answers: list[int] = Field(default_factory=list)  # 正确答案
    hint: str = ""  # 提示（仅在PROMPT_SHOWN状态时提供）
    explanation: str = ""  # 解析（仅终态时提供）
    missed_selections: list[int] = Field(default_factory=list)  # 漏选答案索引
    wrong_selections: list[int] = Field(default_factory=list)  # 错选答案索引
    question_type: str  # 题型
    difficulty: str = ""  # 难度
    knowledge_points: list[str] = Field(default_factory=list)  # 知识点
    source: str = ""  # 来源
    score: int = 0  # 分值
    result_type: ResultType | None = None
    attempt_quality: float = Field(default=0.0, ge=0.0, le=1.0)
    created_at: int  # 创建时间
    updated_at: int  # 更新时间
