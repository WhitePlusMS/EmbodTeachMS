"""作业判分子模块：题目获取、答案验证与自动判分。

仅组合 HomeworkModule 内部使用的 HomeworkQuestion 数据类型与判相关纯逻辑，
不包含作业草稿保存、提交或统计等业务编排。
"""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass

from app.common.errors import BusinessError
from app.teaching_classes.practice import check_answer_correct


logger = logging.getLogger("course_agent.homework_grading")


@dataclass(frozen=True)
class HomeworkQuestion:
    """仅在判分领域内部使用的题目事实，不直接暴露给 API。"""

    id: str
    question_type: str
    stem: str
    options: list[str]
    knowledge_points: list[str]
    hint: str
    correct_answers: list[int]
    explanation: str


class HomeworkGrading:
    """作业判分子模块：题目加载、答案校验、自动判分。

    职责：
    - get_questions          — 从 homework_questions 关联表加载题目
    - validate_answers       — 校验学习者提交的答案格式与完整性
    - grade                  — 逐题判分（委托 check_answer_correct）
    """

    @staticmethod
    def get_questions(
        connection: sqlite3.Connection, homework_id: str
    ) -> list[HomeworkQuestion]:
        """获取作业关联的题目列表"""
        question_rows = connection.execute(
            """
            SELECT
                cc.id, cq.question_type, cq.stem, cq.options_json,
                cq.knowledge_points_json,
                cq.correct_answers_json, cq.hint, cq.explanation
            FROM homework_questions hq
            JOIN course_contents cc ON cc.id = hq.question_id
            JOIN course_content_questions cq ON cq.content_id = cc.id
            WHERE hq.homework_id = ?
            ORDER BY hq.ordinal ASC
            """,
            (homework_id,),
        ).fetchall()

        questions: list[HomeworkQuestion] = []
        for row in question_rows:
            questions.append(
                HomeworkQuestion(
                    id=row["id"],
                    question_type=row["question_type"],
                    stem=row["stem"],
                    options=json.loads(row["options_json"]),
                    knowledge_points=json.loads(row["knowledge_points_json"]),
                    hint=row["hint"],
                    correct_answers=json.loads(row["correct_answers_json"]),
                    explanation=row["explanation"],
                )
            )

        return questions

    @staticmethod
    def validate_answers(
        answers: dict[str, list[int]], questions: list[HomeworkQuestion]
    ) -> None:
        """验证作业答案格式"""
        question_ids = {q.id for q in questions}

        for question_id, answer_indices in answers.items():
            if question_id not in question_ids:
                raise BusinessError(
                    status_code=400,
                    code="INVALID_QUESTION_ID",
                    message=f"题目ID {question_id} 不存在",
                )

            if not isinstance(answer_indices, list):
                raise BusinessError(
                    status_code=400,
                    code="INVALID_ANSWER_FORMAT",
                    message=f"题目 {question_id} 的答案必须是列表格式",
                )
            if not answer_indices:
                raise BusinessError(
                    status_code=400,
                    code="EMPTY_HOMEWORK_ANSWER",
                    message=f"题目 {question_id} 的答案不能为空",
                )
            if len(answer_indices) != len(set(answer_indices)):
                raise BusinessError(
                    status_code=400,
                    code="DUPLICATE_ANSWER_INDEX",
                    message=f"题目 {question_id} 包含重复选项",
                )

            # 获取题目选项数量
            question = next((q for q in questions if q.id == question_id), None)
            if question:
                if any(index >= len(question.options) for index in answer_indices):
                    raise BusinessError(
                        status_code=400,
                        code="INVALID_ANSWER_INDEX",
                        message=f"题目 {question_id} 的答案索引超出选项范围",
                    )

        if not questions or set(answers) != question_ids:
            raise BusinessError(
                status_code=400,
                code="INCOMPLETE_HOMEWORK_ANSWERS",
                message="作业没有可提交的客观题或存在未回答题目",
            )

    @staticmethod
    def grade(
        answers: dict[str, list[int]], questions: list[HomeworkQuestion]
    ) -> dict[str, object]:
        """判分作业"""
        from app.teaching_classes.models import HomeworkQuestionResultView

        total_score = 0
        correct_count = 0
        grading = {}
        detailed_questions = []

        for question in questions:
            question_id = question.id
            user_answers = answers.get(question_id, [])
            correct_answers = question.correct_answers
            explanation = question.explanation

            # 核对答案
            is_correct = check_answer_correct(user_answers, correct_answers)
            score = 1 if is_correct else 0

            total_score += score
            if is_correct:
                correct_count += 1

            # 记录判分详情
            grading[question_id] = {
                "user_answers": user_answers,
                "correct_answers": correct_answers,
                "is_correct": is_correct,
                "score": score,
                "explanation": explanation,
            }

            # 构建题目详情
            question_detail = HomeworkQuestionResultView(
                id=question_id,
                type=question.question_type,
                stem=question.stem,
                options=question.options,
                hint=question.hint,
                user_answers=user_answers,
                correct_answers=correct_answers,
                is_correct=is_correct,
                score=score,
                explanation=explanation,
            )
            detailed_questions.append(question_detail)

        return {
            "total_score": total_score,
            "correct_count": correct_count,
            "grading": grading,
            "questions": detailed_questions,
        }
