"""基准练习状态机实现"""

import time
from typing import Optional

from app.common.errors import BusinessError
from app.teaching_classes.baseline_practice_models import (
    BaselinePracticeStatus,
    BaselinePracticeResult,
    BaselinePracticeDetail,
)
from app.teaching_classes.mastery_models import ResultType


class BaselinePracticeError(BusinessError):
    """基准练习业务错误"""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(status_code=400, code=code, message=message)


class BaselinePracticeStateMachine:
    """基准练习状态机"""

    def __init__(
        self,
        learner_id: str,
        class_id: str,
        content_id: str,
        correct_answers: list[int],
        explanation: str,
        question_type: str,
        difficulty: str = "",
        knowledge_points: list[str] | None = None,
        source: str = "",
        score: int = 0,
    ):
        """初始化状态机

        Args:
            learner_id: 学习者ID
            class_id: 班级ID
            content_id: 内容ID
            correct_answers: 正确答案索引列表
            explanation: 解析说明
            question_type: 题型
            difficulty: 难度
            knowledge_points: 知识点列表
            source: 来源
            score: 分值
        """
        self.learner_id = learner_id
        self.class_id = class_id
        self.content_id = content_id
        self.correct_answers = sorted(set(correct_answers))
        self.explanation = explanation
        self.question_type = question_type
        self.difficulty = difficulty
        self.knowledge_points = knowledge_points or []
        self.source = source
        self.score = score

        # 状态相关
        self.status = BaselinePracticeStatus.INITIAL
        self.first_attempt_answers: list[int] = []
        self.second_attempt_answers: list[int] = []
        self.final_answers: list[int] = []
        self.hint_shown = False
        self.created_at = int(time.time())
        self.updated_at = self.created_at

    def _normalize_answers(self, answers: list[int]) -> list[int]:
        """规范化答案：去重并排序"""
        return sorted(set(answers))

    def _calculate_missed_selections(self, submitted_answers: list[int]) -> list[int]:
        """计算漏选的正确答案"""
        return [answer for answer in self.correct_answers if answer not in submitted_answers]

    def _calculate_wrong_selections(self, submitted_answers: list[int]) -> list[int]:
        """计算错选的答案"""
        return [answer for answer in submitted_answers if answer not in self.correct_answers]

    def result_type(self) -> ResultType | None:
        """终态结果的唯一推导入口。"""
        if self.status == BaselinePracticeStatus.ABANDONED:
            return ResultType.ABANDONED
        if self.status != BaselinePracticeStatus.COMPLETED:
            return None
        if self._normalize_answers(self.first_attempt_answers) == self.correct_answers:
            return ResultType.FIRST_CORRECT
        if self._normalize_answers(self.final_answers) == self.correct_answers:
            return ResultType.HINT_CORRECT
        return ResultType.FINAL_WRONG

    def _calculate_attempt_quality(self) -> float:
        """面向练习反馈的作答质量，不参与掌握度证据类型加权。"""
        return {
            ResultType.FIRST_CORRECT: 1.0,
            ResultType.HINT_CORRECT: 0.8,
            ResultType.FINAL_WRONG: 0.5,
            ResultType.ABANDONED: 0.0,
            None: 0.0,
        }[self.result_type()]

    def submit_answer(self, selected_answers: list[int]) -> BaselinePracticeResult:
        """提交答案

        Args:
            selected_answers: 选中的答案索引列表

        Returns:
            BaselinePracticeResult: 提交结果

        Raises:
            BaselinePracticeError: 如果状态不允许提交或答案为空
        """
        # 检查状态是否允许提交
        if self.status in [BaselinePracticeStatus.COMPLETED, BaselinePracticeStatus.ABANDONED]:
            raise BaselinePracticeError(
                code="INVALID_STATUS",
                message=f"当前状态 {self.status} 不允许提交答案"
            )

        # 检查答案是否为空
        if not selected_answers:
            raise BaselinePracticeError(
                code="EMPTY_ANSWER",
                message="答案不能为空"
            )

        # 规范化答案
        normalized_answers = self._normalize_answers(selected_answers)

        # 更新状态
        self.updated_at = int(time.time())

        if self.status == BaselinePracticeStatus.INITIAL:
            # 第一次提交
            self.first_attempt_answers = normalized_answers

            if normalized_answers == self.correct_answers:
                # 第一次正确
                self.status = BaselinePracticeStatus.COMPLETED
                self.final_answers = normalized_answers
                is_correct = True
                hint = ""
            else:
                # 第一次错误
                self.status = BaselinePracticeStatus.PROMPT_SHOWN
                is_correct = False
                hint = "答案不正确，请检查后再试一次"

        elif self.status == BaselinePracticeStatus.PROMPT_SHOWN:
            # 第二次提交
            self.second_attempt_answers = normalized_answers
            self.status = BaselinePracticeStatus.COMPLETED
            self.final_answers = normalized_answers
            is_correct = normalized_answers == self.correct_answers
            hint = ""

        else:
            # 理论上不会到达这里
            raise BaselinePracticeError(
                code="UNEXPECTED_STATUS",
                message=f"意外的状态: {self.status}"
            )

        # 构建结果
        result = BaselinePracticeResult(
            is_correct=is_correct,
            status=self.status,
            correct_answers=self.correct_answers if self.status == BaselinePracticeStatus.COMPLETED else [],
            explanation=self.explanation if self.status == BaselinePracticeStatus.COMPLETED else "",
            hint=hint,
            can_submit_again=self.status != BaselinePracticeStatus.COMPLETED
        )

        return result

    def abandon(self) -> BaselinePracticeResult:
        """放弃练习

        Returns:
            BaselinePracticeResult: 放弃结果
        """
        self.updated_at = int(time.time())

        if self.status == BaselinePracticeStatus.ABANDONED:
            # 幂等处理：已经是放弃状态
            result = BaselinePracticeResult(
                is_correct=False,
                status=self.status,
                correct_answers=[],
                explanation="",
                hint="",
                can_submit_again=False
            )
        elif self.status == BaselinePracticeStatus.COMPLETED:
            raise BaselinePracticeError(
                code="INVALID_STATUS",
                message="已完成的基准练习不能主动结束",
            )
        else:
            # 更新为放弃状态
            self.status = BaselinePracticeStatus.ABANDONED

            result = BaselinePracticeResult(
                is_correct=False,
                status=self.status,
                correct_answers=[],
                explanation="",
                hint="",
                can_submit_again=False
            )

        return result

    def get_detail(self) -> BaselinePracticeDetail:
        """获取练习详情

        Returns:
            BaselinePracticeDetail: 练习详情
        """
        # 计算漏选和错选
        missed_selections: list[int] = []
        wrong_selections: list[int] = []

        if self.final_answers:
            missed_selections = self._calculate_missed_selections(self.final_answers)
            wrong_selections = self._calculate_wrong_selections(self.final_answers)
        elif self.second_attempt_answers:
            missed_selections = self._calculate_missed_selections(self.second_attempt_answers)
            wrong_selections = self._calculate_wrong_selections(self.second_attempt_answers)
        elif self.first_attempt_answers:
            missed_selections = self._calculate_missed_selections(self.first_attempt_answers)
            wrong_selections = self._calculate_wrong_selections(self.first_attempt_answers)

        # 确定是否正确（仅终态时有效）
        is_correct: Optional[bool] = None
        if self.status == BaselinePracticeStatus.COMPLETED:
            is_correct = self._normalize_answers(self.final_answers) == self.correct_answers

        # 构建详情
        detail = BaselinePracticeDetail(
            learner_id=self.learner_id,
            class_id=self.class_id,
            content_id=self.content_id,
            status=self.status,
            first_attempt_answers=self.first_attempt_answers,
            second_attempt_answers=self.second_attempt_answers,
            final_answers=self.final_answers,
            is_correct=is_correct,
            correct_answers=self.correct_answers if self.status in [BaselinePracticeStatus.COMPLETED, BaselinePracticeStatus.ABANDONED] else [],
            hint="答案不正确，请检查后再试一次" if self.status == BaselinePracticeStatus.PROMPT_SHOWN else "",
            explanation=self.explanation if self.status in [BaselinePracticeStatus.COMPLETED, BaselinePracticeStatus.ABANDONED] else "",
            missed_selections=missed_selections,
            wrong_selections=wrong_selections,
            question_type=self.question_type,
            difficulty=self.difficulty,
            knowledge_points=self.knowledge_points,
            source=self.source,
            score=self.score,
            result_type=self.result_type(),
            attempt_quality=self._calculate_attempt_quality(),
            created_at=self.created_at,
            updated_at=self.updated_at
        )

        return detail
