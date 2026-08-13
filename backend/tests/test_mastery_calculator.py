"""任务14掌握度纯计算规则测试。"""

import pytest
from pydantic import ValidationError

from app.teaching_classes.mastery_calculator import MasteryCalculator
from app.teaching_classes.mastery_models import (
    Evidence,
    EvidenceType,
    MasteryCalculationInput,
    MasteryLevel,
    ResultType,
)


def evidence(
    evidence_id: str,
    question_id: str,
    result_type: ResultType,
    created_at: int,
    *,
    evidence_type: EvidenceType = EvidenceType.BASELINE,
) -> Evidence:
    score = {
        ResultType.FIRST_CORRECT: 2,
        ResultType.HINT_CORRECT: 1,
        ResultType.FINAL_WRONG: -2,
        ResultType.ABANDONED: 0,
    }[result_type]
    return Evidence(
        evidenceId=evidence_id,
        questionId=question_id,
        evidenceType=evidence_type,
        resultType=result_type,
        score=score,
        evidenceCoefficient=2.0 if evidence_type == EvidenceType.BASELINE else 1.0,
        createdAt=created_at,
        isFinal=True,
    )


def calculate(evidences: list[Evidence], current: MasteryLevel = MasteryLevel.UNLEARNED):
    return MasteryCalculator.calculate_mastery(
        MasteryCalculationInput(
            learnerId="learner",
            classId="class",
            knowledgePointId="kp",
            currentMasteryLevel=current,
            allEvidence=evidences,
        )
    )


def test_thresholds_and_one_level_upgrade() -> None:
    """测试阈值和逐级升级"""
    # 无证据时保持unlearned
    assert calculate([]).mastery_level == MasteryLevel.UNLEARNED

    # 3题但分数不足
    three_low_score = [evidence(str(i), f"q{i}", ResultType.HINT_CORRECT, i) for i in range(3)]
    assert calculate(three_low_score).mastery_level == MasteryLevel.CONSOLIDATING

    # 3题且分数达标
    three = [evidence(str(i), f"q{i}", ResultType.FIRST_CORRECT, i) for i in range(3)]
    assert calculate(three).mastery_level == MasteryLevel.CONSOLIDATING
    assert calculate(three, MasteryLevel.CONSOLIDATING).mastery_level == MasteryLevel.BASIC_MASTERY

    # 5题但首次正确不足
    five_low_first = [
        evidence("1", "q1", ResultType.FIRST_CORRECT, 1),
        evidence("2", "q2", ResultType.FIRST_CORRECT, 2),
        evidence("3", "q3", ResultType.HINT_CORRECT, 3),
        evidence("4", "q4", ResultType.HINT_CORRECT, 4),
        evidence("5", "q5", ResultType.HINT_CORRECT, 5),
    ]
    assert calculate(five_low_first, MasteryLevel.BASIC_MASTERY).mastery_level == MasteryLevel.BASIC_MASTERY

    # 5题且全部达标
    five = [evidence(str(i), f"q{i}", ResultType.FIRST_CORRECT, i) for i in range(5)]
    assert calculate(five, MasteryLevel.BASIC_MASTERY).mastery_level == MasteryLevel.PROFICIENT_MASTERY


def test_latest_duplicate_and_recent_six_are_deterministic() -> None:
    """测试同题去重和最近6题确定性"""
    # 同题去重测试
    duplicate_old = evidence("a", "same", ResultType.FINAL_WRONG, 10)
    duplicate_new = evidence("b", "same", ResultType.FIRST_CORRECT, 10)
    result = calculate([duplicate_old, duplicate_new])
    assert len(result.used_evidence) == 1
    assert result.used_evidence[0].evidence_id == "b"  # 应该保留更新的证据

    # 最近6题测试
    recent = [evidence(str(i), f"q{i}", ResultType.FIRST_CORRECT, 20 + i) for i in range(7)]
    result = calculate(recent)
    assert len(result.used_evidence) == 6
    assert result.used_evidence[0].question_id == "q6"  # 时间戳最大的在最前面


def test_downgrade_requires_two_recent_final_errors_and_never_unlearns() -> None:
    """测试降级条件和已有证据不回到unlearned"""
    # 满足降级条件：最近3题有2题错误
    two_errors = [
        evidence("1", "q1", ResultType.FINAL_WRONG, 3),
        evidence("2", "q2", ResultType.FINAL_WRONG, 2),
        evidence("3", "q3", ResultType.FIRST_CORRECT, 1),
    ]
    result = calculate(two_errors, MasteryLevel.PROFICIENT_MASTERY)
    assert result.mastery_level == MasteryLevel.BASIC_MASTERY

    # 不满足降级条件：最近3题只有1题错误
    one_error = [
        evidence("1", "q1", ResultType.FINAL_WRONG, 3),
        evidence("2", "q2", ResultType.FIRST_CORRECT, 2),
        evidence("3", "q3", ResultType.FIRST_CORRECT, 1),
    ]
    assert calculate(one_error, MasteryLevel.BASIC_MASTERY).mastery_level == MasteryLevel.BASIC_MASTERY

    # 已有证据后不回到unlearned
    mixed = [
        evidence("1", "q1", ResultType.FINAL_WRONG, 3),
        evidence("2", "q2", ResultType.FINAL_WRONG, 2),
    ]
    result = calculate(mixed, MasteryLevel.CONSOLIDATING)
    assert result.mastery_level == MasteryLevel.CONSOLIDATING  # 不回到unlearned


def test_evidence_type_and_coefficient_are_strict() -> None:
    """测试证据类型和系数的严格验证"""
    # 个性化证据系数错误
    with pytest.raises(ValidationError):
        Evidence(
            evidenceId="x",
            questionId="q",
            evidenceType=EvidenceType.PERSONALIZED,
            resultType=ResultType.FIRST_CORRECT,
            score=2,
            evidenceCoefficient=2,
            createdAt=1,
            isFinal=True,
        )

    # 非法证据类型
    with pytest.raises(ValidationError):
        Evidence(
            evidenceId="x",
            questionId="q",
            evidenceType="classroom",
            resultType="first_correct",
            score=2,
            evidenceCoefficient=1,
            createdAt=1,
            isFinal=True,
        )

    # 分数与结果类型不匹配
    with pytest.raises(ValidationError):
        Evidence(
            evidenceId="x",
            questionId="q",
            evidenceType=EvidenceType.BASELINE,
            resultType=ResultType.FIRST_CORRECT,
            score=1,  # 应为2
            evidenceCoefficient=2.0,
            createdAt=1,
            isFinal=True,
        )


def test_illegal_evidence_types_rejected() -> None:
    """测试非法证据类型被拒绝"""
    with pytest.raises(ValidationError):
        Evidence(
            evidenceId="x",
            questionId="q",
            evidenceType="homework",
            resultType=ResultType.FIRST_CORRECT,
            score=2,
            evidenceCoefficient=1.0,
            createdAt=1,
            isFinal=True,
        )


def test_personalized_evidence_works() -> None:
    """测试个性化证据正常工作"""
    # 个性化证据系数为1.0
    personalized = evidence("1", "q1", ResultType.FIRST_CORRECT, 1, evidence_type=EvidenceType.PERSONALIZED)
    result = calculate([personalized])
    assert result.weighted_score == 2.0  # 2 * 1.0

    # 基准证据系数为2.0
    baseline = evidence("2", "q2", ResultType.FIRST_CORRECT, 2, evidence_type=EvidenceType.BASELINE)
    result = calculate([baseline])
    assert result.weighted_score == 4.0  # 2 * 2.0


def test_replay_mastery_replays_prefixes_step_by_step() -> None:
    """测试 replay_mastery 逐条重放：单次钳制不变量封闭在 calculator 内"""
    # 无证据返回 None
    assert MasteryCalculator.replay_mastery([]) is None

    five = [evidence(str(i), f"q{i}", ResultType.FIRST_CORRECT, i + 1) for i in range(5)]

    # 单次调用只钳一级：unlearned 直接给全量只能到 consolidating
    assert calculate(five).mastery_level == MasteryLevel.CONSOLIDATING

    # 逐条重放才能逐级升到熟练掌握
    result = MasteryCalculator.replay_mastery(five)
    assert result is not None
    assert result.mastery_level == MasteryLevel.PROFICIENT_MASTERY

    # 输入乱序时按(created_at, evidence_id)排序重放，结果一致
    shuffled = [five[2], five[4], five[0], five[3], five[1]]
    shuffled_result = MasteryCalculator.replay_mastery(shuffled)
    assert shuffled_result is not None
    assert shuffled_result.mastery_level == MasteryLevel.PROFICIENT_MASTERY


def test_replay_mastery_applies_downgrade_across_evidence() -> None:
    """测试 replay_mastery 跨证据序列应用降级规则"""
    sequence = [evidence(str(i), f"q{i}", ResultType.FIRST_CORRECT, i + 1) for i in range(5)]
    sequence += [
        evidence("w1", "qw1", ResultType.FINAL_WRONG, 6),
        evidence("w2", "qw2", ResultType.FINAL_WRONG, 7),
    ]

    result = MasteryCalculator.replay_mastery(sequence)
    assert result is not None
    # 最近三题中两题最终错误，允许从熟练掌握降一级
    assert result.mastery_level == MasteryLevel.BASIC_MASTERY
