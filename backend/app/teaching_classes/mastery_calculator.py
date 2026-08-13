from typing import Literal

from .mastery_models import (
    Evidence,
    MasteryCalculationInput,
    MasteryCalculationResult,
    MasteryLevel,
    ResultType,
)


class MasteryCalculator:
    """掌握度纯计算核心"""

    @classmethod
    def replay_mastery(cls, all_evidence: list[Evidence]) -> MasteryCalculationResult | None:
        """按时间顺序逐条重放全部证据，返回最终掌握度；无证据时返回 None。

        「每条新证据最多升/降一级」的钳制只在单次计算内生效，因此多条证据
        必须逐条前缀重放才能得到正确的最终级别。该不变量封闭在本方法内：
        调用方只需提供证据，无需了解 current_mastery_level 的传递约定。
        """
        ordered_evidence = sorted(
            all_evidence,
            key=lambda evidence: (evidence.created_at, evidence.evidence_id),
        )
        current_level = MasteryLevel.UNLEARNED
        result = None
        for index in range(1, len(ordered_evidence) + 1):
            result = cls._calculate(current_level, ordered_evidence[:index])
            current_level = result.mastery_level
        return result

    @staticmethod
    def calculate_mastery(input_data: MasteryCalculationInput) -> MasteryCalculationResult:
        """
        单次计算掌握度级别

        规则：
        1. 按同一 question_id 只保留最新证据
        2. 取最近六道不同题
        3. weighted_score = score * evidence_coefficient
        4. 基本掌握：至少3道不同题且加权总分>=4
        5. 熟练掌握：至少5道不同题、加权总分>=10且至少3道首次正确
        6. 每条新证据最多升/降一级（钳制只在本调用内生效一次，
           由多条证据推最终级别请使用 replay_mastery 逐条重放）
        7. 最近三道不同题中至少两道最终错误才允许下降一级
        8. 已有证据后不回到 unlearned
        """
        return MasteryCalculator._calculate(
            input_data.current_mastery_level,
            input_data.all_evidence,
        )

    @staticmethod
    def _calculate(
        current_level: MasteryLevel,
        all_evidence: list[Evidence],
    ) -> MasteryCalculationResult:
        """单次计算：在给定当前级别上应用一次级别钳制。"""

        # 1. 预处理证据：按question_id去重，保留最新的
        processed_evidence = MasteryCalculator._preprocess_evidence(all_evidence)

        # 2. 获取最近六道不同题
        recent_evidence = MasteryCalculator._get_recent_evidence(processed_evidence)

        # 3. 计算各项指标
        weighted_score = MasteryCalculator._calculate_weighted_score(recent_evidence)
        recent_evidence_count = len(recent_evidence)
        first_correct_count = MasteryCalculator._count_first_correct(recent_evidence)

        # 4. 确定新的掌握度级别
        new_level = MasteryCalculator._determine_mastery_level(
            recent_evidence_count,
            weighted_score,
            first_correct_count,
            current_level
        )

        # 5. 应用级别变化限制
        final_level = MasteryCalculator._apply_level_change_limits(
            new_level,
            current_level,
            recent_evidence
        )

        # 6. 计算级别变化
        level_change = MasteryCalculator._calculate_level_change(
            current_level,
            final_level
        )

        return MasteryCalculationResult(
            mastery_level=final_level,
            weighted_score=weighted_score,
            recent_evidence_count=recent_evidence_count,
            first_correct_count=first_correct_count,
            used_evidence=recent_evidence,
            level_change=level_change
        )

    @staticmethod
    def _preprocess_evidence(evidence_list: list[Evidence]) -> list[Evidence]:
        """预处理证据：按question_id去重，按(created_at, evidence_id)的最大值保留"""
        evidence_by_question: dict[str, Evidence] = {}

        for evidence in evidence_list:
            if evidence.question_id not in evidence_by_question:
                evidence_by_question[evidence.question_id] = evidence
            else:
                # 比较(created_at, evidence_id)元组，取最大值
                current_max = evidence_by_question[evidence.question_id]
                current_key = (current_max.created_at, current_max.evidence_id)
                new_key = (evidence.created_at, evidence.evidence_id)

                if new_key > current_key:
                    evidence_by_question[evidence.question_id] = evidence

        return list(evidence_by_question.values())

    @staticmethod
    def _get_recent_evidence(evidence_list: list[Evidence]) -> list[Evidence]:
        """获取最近六道不同题，按(created_at, evidence_id)稳定排序"""
        # 按(created_at, evidence_id)降序排序，确保稳定顺序
        sorted_evidence = sorted(
            evidence_list,
            key=lambda e: (e.created_at, e.evidence_id),
            reverse=True
        )

        # 取前6条（如果不足6条则取全部）
        return sorted_evidence[:6]

    @staticmethod
    def _calculate_weighted_score(evidence_list: list[Evidence]) -> float:
        """计算加权总分"""
        return sum(evidence.score * evidence.evidence_coefficient for evidence in evidence_list)

    @staticmethod
    def _count_first_correct(evidence_list: list[Evidence]) -> int:
        """统计首次正确的题目数量"""
        return sum(1 for evidence in evidence_list if evidence.result_type == ResultType.FIRST_CORRECT)

    @staticmethod
    def _determine_mastery_level(
        evidence_count: int,
        weighted_score: float,
        first_correct_count: int,
        current_level: MasteryLevel
    ) -> MasteryLevel:
        """根据指标确定掌握度级别"""

        # 无证据时保持当前级别（如果已有证据）或返回未学习
        if evidence_count == 0:
            return MasteryLevel.UNLEARNED if current_level == MasteryLevel.UNLEARNED else current_level

        # 检查是否满足熟练掌握条件
        if (evidence_count >= 5 and
            weighted_score >= 10 and
            first_correct_count >= 3):
            return MasteryLevel.PROFICIENT_MASTERY

        # 检查是否满足基本掌握条件
        if evidence_count >= 3 and weighted_score >= 4:
            return MasteryLevel.BASIC_MASTERY

        # 有证据但不足以达到基本掌握
        if evidence_count > 0:
            return MasteryLevel.CONSOLIDATING

        return MasteryLevel.UNLEARNED

    @staticmethod
    def _apply_level_change_limits(
        new_level: MasteryLevel,
        current_level: MasteryLevel,
        recent_evidence: list[Evidence]
    ) -> MasteryLevel:
        """应用级别变化限制"""

        # 如果级别不变，直接返回
        if new_level == current_level:
            return new_level

        # 检查是否允许升级（最多升一级）
        if MasteryCalculator._is_level_increase(current_level, new_level):
            return MasteryCalculator._limit_level_increase(current_level, new_level)

        # 检查是否允许降级
        if MasteryCalculator._is_level_decrease(current_level, new_level):
            return MasteryCalculator._limit_level_decrease(current_level, new_level, recent_evidence)

        return current_level

    @staticmethod
    def _is_level_increase(current: MasteryLevel, new: MasteryLevel) -> bool:
        """判断是否为升级"""
        levels = [MasteryLevel.UNLEARNED, MasteryLevel.CONSOLIDATING,
                 MasteryLevel.BASIC_MASTERY, MasteryLevel.PROFICIENT_MASTERY]
        return levels.index(new) > levels.index(current)

    @staticmethod
    def _is_level_decrease(current: MasteryLevel, new: MasteryLevel) -> bool:
        """判断是否为降级"""
        levels = [MasteryLevel.UNLEARNED, MasteryLevel.CONSOLIDATING,
                 MasteryLevel.BASIC_MASTERY, MasteryLevel.PROFICIENT_MASTERY]
        return levels.index(new) < levels.index(current)

    @staticmethod
    def _limit_level_increase(current: MasteryLevel, new: MasteryLevel) -> MasteryLevel:
        """限制升级：最多升一级"""
        levels = [MasteryLevel.UNLEARNED, MasteryLevel.CONSOLIDATING,
                 MasteryLevel.BASIC_MASTERY, MasteryLevel.PROFICIENT_MASTERY]

        current_index = levels.index(current)
        new_index = levels.index(new)

        # 最多升一级
        if new_index - current_index > 1:
            return levels[current_index + 1]

        return new

    @staticmethod
    def _limit_level_decrease(
        current: MasteryLevel,
        new: MasteryLevel,
        recent_evidence: list[Evidence]
    ) -> MasteryLevel:
        """限制降级：需要满足条件"""

        # 已有证据后不回到unlearned
        if len(recent_evidence) > 0 and new == MasteryLevel.UNLEARNED:
            # 强制回到最低的已学习级别
            return MasteryLevel.CONSOLIDATING

        # 检查最近三道不同题中是否至少两道最终错误
        recent_three = recent_evidence[:3]
        final_wrong_count = sum(1 for e in recent_three if e.result_type == ResultType.FINAL_WRONG)

        # 降级条件：最近3题中至少有2题最终错误
        if final_wrong_count >= 2:
            # 最多降一级
            levels = [MasteryLevel.UNLEARNED, MasteryLevel.CONSOLIDATING,
                     MasteryLevel.BASIC_MASTERY, MasteryLevel.PROFICIENT_MASTERY]
            current_index = levels.index(current)
            new_index = levels.index(new)

            if current_index - new_index > 1:
                return levels[current_index - 1]
            return new

        # 不满足降级条件，保持当前级别
        return current

    @staticmethod
    def _calculate_level_change(current: MasteryLevel, new: MasteryLevel) -> Literal[-1, 0, 1]:
        """计算级别变化"""
        levels = [MasteryLevel.UNLEARNED, MasteryLevel.CONSOLIDATING,
                 MasteryLevel.BASIC_MASTERY, MasteryLevel.PROFICIENT_MASTERY]

        current_index = levels.index(current)
        new_index = levels.index(new)

        if new_index > current_index:
            return 1
        elif new_index < current_index:
            return -1
        else:
            return 0
