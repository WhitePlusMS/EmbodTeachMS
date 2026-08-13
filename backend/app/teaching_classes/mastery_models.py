from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel


class MasteryLevel(StrEnum):
    """掌握度级别"""
    UNLEARNED = "unlearned"  # 未学习
    CONSOLIDATING = "consolidating"  # 待巩固
    BASIC_MASTERY = "basic_mastery"  # 基本掌握
    PROFICIENT_MASTERY = "proficient_mastery"  # 熟练掌握


class EvidenceType(StrEnum):
    """证据类型"""
    BASELINE = "baseline"  # 基准练习
    PERSONALIZED = "personalized"  # 个性化练习


class ResultType(StrEnum):
    """结果类型"""
    FIRST_CORRECT = "first_correct"  # 首次正确
    HINT_CORRECT = "hint_correct"  # 提示后正确
    FINAL_WRONG = "final_wrong"  # 最终错误
    ABANDONED = "abandoned"  # 放弃


RESULT_SCORES: dict[ResultType, int] = {
    ResultType.FIRST_CORRECT: 2,
    ResultType.HINT_CORRECT: 1,
    ResultType.FINAL_WRONG: -2,
    ResultType.ABANDONED: 0,
}

EVIDENCE_COEFFICIENTS: dict[EvidenceType, float] = {
    EvidenceType.BASELINE: 2.0,
    EvidenceType.PERSONALIZED: 1.0,
}


class Evidence(BaseModel):
    """掌握度证据"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    evidence_id: str = Field(min_length=1, description="证据ID，用于去重时的tie-break")
    question_id: str = Field(min_length=1, description="题目ID")
    evidence_type: EvidenceType = Field(description="证据类型")
    result_type: ResultType = Field(description="结果类型")
    score: int = Field(description="原始分数", ge=-2, le=2)
    evidence_coefficient: float = Field(description="证据系数", ge=1, le=2)
    created_at: int = Field(description="创建时间戳", ge=0)
    is_final: bool = Field(description="是否为最终状态")

    @classmethod
    def from_result(
        cls,
        *,
        evidence_id: str,
        question_id: str,
        evidence_type: EvidenceType,
        result_type: ResultType,
        created_at: int,
    ) -> "Evidence":
        """由结果事实构造一致的分数与证据类型系数。"""
        return cls(
            evidence_id=evidence_id,
            question_id=question_id,
            evidence_type=evidence_type,
            result_type=result_type,
            score=RESULT_SCORES[result_type],
            evidence_coefficient=EVIDENCE_COEFFICIENTS[evidence_type],
            created_at=created_at,
            is_final=True,
        )

    @field_validator("score")
    @classmethod
    def validate_score(cls, score: int, info) -> int:
        """根据结果类型验证分数"""
        result_type = info.data.get("result_type")

        # 验证分数与结果类型的匹配关系
        if result_type in RESULT_SCORES:
            if score != RESULT_SCORES[result_type]:
                raise ValueError(f"结果类型 {result_type} 对应的分数应为 {RESULT_SCORES[result_type]}, 但实际为 {score}")
        else:
            raise ValueError(f"不支持的证据结果类型: {result_type}")

        return score

    @field_validator("evidence_coefficient")
    @classmethod
    def validate_evidence_coefficient(cls, coefficient: float, info) -> float:
        """验证证据系数与证据类型的匹配关系"""
        evidence_type = info.data.get("evidence_type")

        if evidence_type in EVIDENCE_COEFFICIENTS:
            if coefficient != EVIDENCE_COEFFICIENTS[evidence_type]:
                raise ValueError(f"证据类型 {evidence_type} 对应的证据系数应为 {EVIDENCE_COEFFICIENTS[evidence_type]}, 但实际为 {coefficient}")
        else:
            raise ValueError(f"不支持的证据类型: {evidence_type}")

        return coefficient


class MasteryCalculationInput(BaseModel):
    """掌握度计算输入"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    learner_id: str = Field(min_length=1, description="学习者ID")
    class_id: str = Field(min_length=1, description="班级ID")
    knowledge_point_id: str = Field(min_length=1, description="知识点ID")
    current_mastery_level: MasteryLevel = Field(default=MasteryLevel.UNLEARNED, description="当前掌握度级别")
    all_evidence: list[Evidence] = Field(default_factory=list, description="所有相关证据")


class MasteryCalculationResult(BaseModel):
    """掌握度计算结果"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    mastery_level: MasteryLevel = Field(description="计算后的掌握度级别")
    weighted_score: float = Field(description="加权总分")
    recent_evidence_count: int = Field(description="最近有效证据数量")
    first_correct_count: int = Field(description="首次正确题目数量")
    used_evidence: list[Evidence] = Field(description="用于计算的证据列表")
    level_change: Literal[-1, 0, 1] = Field(description="级别变化：-1=下降，0=不变，1=上升")

    @field_validator("level_change")
    @classmethod
    def validate_level_change(cls, change: int) -> int:
        """验证级别变化范围"""
        if change not in [-1, 0, 1]:
            raise ValueError("级别变化只能是-1、0或1")
        return change
