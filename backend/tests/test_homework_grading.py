"""Homework判分逻辑纯单元测试，不依赖数据库或 FastAPI。"""
from __future__ import annotations

from app.teaching_classes.homework_grading import HomeworkGrading, HomeworkQuestion
from app.teaching_classes.practice import check_answer_correct


class TestCheckAnswerCorrect:
    """check_answer_correct 纯函数：正确答案匹配逻辑。"""

    def test_exact_match_single_choice(self) -> None:
        assert check_answer_correct([0], [0]) is True

    def test_exact_match_multiple_choice(self) -> None:
        assert check_answer_correct([0, 2], [0, 2]) is True

    def test_exact_match_order_independent(self) -> None:
        assert check_answer_correct([2, 0], [0, 2]) is True

    def test_wrong_answer(self) -> None:
        assert check_answer_correct([1], [0]) is False

    def test_partial_match(self) -> None:
        # 多选场景：选了部分正确答案但选不全
        assert check_answer_correct([0], [0, 2]) is False

    def test_extra_wrong_answers(self) -> None:
        # 多选场景：选了正确答案但也选了错误答案
        assert check_answer_correct([0, 1], [0]) is False

    def test_no_answers_selected(self) -> None:
        assert check_answer_correct([], [0]) is False

    def test_multiple_correct_answers_with_reversed_order(self) -> None:
        assert check_answer_correct([3, 1, 2], [1, 2, 3]) is True

    def test_all_answers_wrong(self) -> None:
        assert check_answer_correct([4, 5], [0, 2]) is False


class TestHomeworkGradingLogic:
    """HomeworkGrading.grade 判分逻辑的白盒校验。"""

    def test_grading_single_question_correct(self) -> None:
        questions = [
            HomeworkQuestion(id="q1", question_type="single_choice", stem="test", options=["A", "B"], knowledge_points=[], hint="", correct_answers=[0], explanation="correct"),
        ]
        result = HomeworkGrading.grade({"q1": [0]}, questions)

        assert result["total_score"] == 1
        assert result["correct_count"] == 1
        assert result["grading"]["q1"]["is_correct"] is True

    def test_grading_all_wrong(self) -> None:
        questions = [
            HomeworkQuestion(id="q1", question_type="single_choice", stem="test", options=["A", "B", "C"], knowledge_points=[], hint="", correct_answers=[1], explanation=""),
            HomeworkQuestion(id="q2", question_type="multiple_choice", stem="test2", options=["A", "B", "C"], knowledge_points=[], hint="", correct_answers=[0, 2], explanation=""),
        ]
        result = HomeworkGrading.grade({"q1": [0], "q2": [1]}, questions)

        assert result["total_score"] == 0
        assert result["correct_count"] == 0

    def test_grading_partial_correct(self) -> None:
        questions = [
            HomeworkQuestion(id="q1", question_type="single_choice", stem="test", options=["A", "B"], knowledge_points=[], hint="", correct_answers=[0], explanation=""),
            HomeworkQuestion(id="q2", question_type="single_choice", stem="test2", options=["A", "B"], knowledge_points=[], hint="", correct_answers=[1], explanation=""),
        ]
        result = HomeworkGrading.grade({"q1": [0], "q2": [0]}, questions)

        assert result["total_score"] == 1
        assert result["correct_count"] == 1
        assert result["grading"]["q1"]["is_correct"] is True
        assert result["grading"]["q2"]["is_correct"] is False

    def test_grading_explanation_included(self) -> None:
        questions = [
            HomeworkQuestion(id="q1", question_type="single_choice", stem="test", options=["A", "B"], knowledge_points=[], hint="", correct_answers=[0], explanation="答案是A"),
        ]
        result = HomeworkGrading.grade({"q1": [0]}, questions)

        assert result["grading"]["q1"]["explanation"] == "答案是A"

    def test_grading_question_detail_view(self) -> None:
        questions = [
            HomeworkQuestion(id="q1", question_type="single_choice", stem="test", options=["A", "B"], knowledge_points=[], hint="hint1", correct_answers=[0], explanation="exp"),
        ]
        result = HomeworkGrading.grade({"q1": [0]}, questions)

        q_details = result["questions"]
        assert len(q_details) == 1
        assert q_details[0].id == "q1"
        assert q_details[0].is_correct is True
        assert q_details[0].score == 1
        assert q_details[0].hint == "hint1"
