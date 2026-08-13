from typing import TypedDict

from app.common.errors import BusinessError
from app.teaching_classes.models import (
    CreateQuestionRequest,
    QuestionReviewStatus,
    QuestionSource,
    QuestionType,
    QuestionView,
    UpdateQuestionRequest,
)


class StoredQuestion(TypedDict):
    id: str
    source: str
    review_status: str
    type: str
    stem: str
    options: list[str]
    answers: list[int]
    knowledge_points: list[str]
    highlight_source_ids: list[str]
    hint: str
    explanation: str
    created_at: int
    updated_at: int


class QuestionReviewModule:
    """集中维护题目不变量、审核迁移和发布门禁。"""

    def to_view(self, question: StoredQuestion) -> QuestionView:
        """将内部题目记录转换为唯一的对外视图。"""
        return QuestionView(
            id=question["id"],
            source=QuestionSource(question["source"]),
            review_status=QuestionReviewStatus(question["review_status"]),
            type=QuestionType(question["type"]),
            stem=question["stem"],
            options=question["options"],
            answers=sorted(question["answers"]),
            knowledge_points=question["knowledge_points"],
            highlight_source_ids=question["highlight_source_ids"],
            hint=question["hint"],
            explanation=question["explanation"],
            created_at=question["created_at"],
            updated_at=question["updated_at"],
        )

    def create_manual(self, request: CreateQuestionRequest, question_id: str, now: int) -> StoredQuestion:
        """创建一条已确认的手工题。"""
        return {
            "id": question_id,
            "source": QuestionSource.MANUAL.value,
            "review_status": QuestionReviewStatus.CONFIRMED.value,
            "type": request.type.value,
            "stem": request.stem,
            "options": request.options,
            "answers": list(request.answers),
            "knowledge_points": request.knowledge_points,
            "highlight_source_ids": request.highlight_source_ids,
            "hint": request.hint,
            "explanation": request.explanation,
            "created_at": now,
            "updated_at": now,
        }

    def update(self, question: StoredQuestion, request: UpdateQuestionRequest, now: int) -> StoredQuestion:
        """更新题目内容但保留来源与审核状态。"""
        return {
            **question,
            "type": request.type.value,
            "stem": request.stem,
            "options": request.options,
            "answers": list(request.answers),
            "knowledge_points": request.knowledge_points,
            "highlight_source_ids": request.highlight_source_ids,
            "hint": request.hint,
            "explanation": request.explanation,
            "updated_at": now,
        }

    def confirm(self, question: StoredQuestion, now: int) -> StoredQuestion:
        """将候选题迁移为已确认题。"""
        if question["source"] != QuestionSource.CANDIDATE.value:
            raise BusinessError(status_code=400, code="INVALID_QUESTION_SOURCE", message="只能确认候选题")
        if question["review_status"] != QuestionReviewStatus.CANDIDATE.value:
            raise BusinessError(status_code=409, code="QUESTION_ALREADY_CONFIRMED", message="候选题已经确认")
        return {**question, "review_status": QuestionReviewStatus.CONFIRMED.value, "updated_at": now}

    def is_publish_unlocked(self, questions: list[StoredQuestion]) -> bool:
        """只有处理完所有候选且至少存在一题已确认时才解锁。"""
        candidates = [question for question in questions if question["source"] == QuestionSource.CANDIDATE.value]
        confirmed_candidates = [question for question in candidates if question["review_status"] == QuestionReviewStatus.CONFIRMED.value]
        has_confirmed_question = any(question["source"] == QuestionSource.MANUAL.value for question in questions) or bool(confirmed_candidates)
        return (not candidates or len(candidates) == len(confirmed_candidates)) and has_confirmed_question
