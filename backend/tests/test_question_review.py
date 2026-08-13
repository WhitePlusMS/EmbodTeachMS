"""QuestionReviewModule 纯单元测试（无数据库依赖）。"""
from __future__ import annotations

from app.teaching_classes.models import (
    CreateQuestionRequest,
    QuestionReviewStatus,
    QuestionSource,
    QuestionType,
    UpdateQuestionRequest,
)
from app.teaching_classes.question_review import QuestionReviewModule, StoredQuestion


def _stored(**overrides: object) -> StoredQuestion:
    """构造完整的 StoredQuestion 固定样本。"""
    base: StoredQuestion = {
        "id": "q-1",
        "source": QuestionSource.MANUAL.value,
        "review_status": QuestionReviewStatus.CONFIRMED.value,
        "type": QuestionType.SINGLE_CHOICE.value,
        "stem": "测试题目",
        "options": ["选项A", "选项B", "选项C"],
        "answers": [0],
        "knowledge_points": ["测试知识点"],
        "highlight_source_ids": ["h-1"],
        "hint": "提示",
        "explanation": "解析",
        "created_at": 1000,
        "updated_at": 1000,
    }
    base.update(**overrides)
    return base


class TestToView:
    def test_to_view_basic(self):
        module = QuestionReviewModule()
        stored = _stored()
        view = module.to_view(stored)
        assert view.id == "q-1"
        assert view.source == QuestionSource.MANUAL
        assert view.review_status == QuestionReviewStatus.CONFIRMED
        assert view.type == QuestionType.SINGLE_CHOICE
        assert view.stem == "测试题目"
        assert view.options == ["选项A", "选项B", "选项C"]
        assert view.answers == [0]
        assert view.knowledge_points == ["测试知识点"]

    def test_to_view_multiple_choice(self):
        module = QuestionReviewModule()
        stored = _stored(
            id="q-2",
            type=QuestionType.MULTIPLE_CHOICE.value,
            answers=[0, 2],
        )
        view = module.to_view(stored)
        assert view.type == QuestionType.MULTIPLE_CHOICE
        assert view.answers == [0, 2]


class TestCreateManual:
    def test_create_manual_confirmed(self):
        module = QuestionReviewModule()
        request = CreateQuestionRequest(
            type=QuestionType.SINGLE_CHOICE,
            stem="新增题目",
            options=["A", "B"],
            answers={1},
            knowledge_points=["KP1"],
            highlight_source_ids=[],
        )
        result = module.create_manual(request, "new-q-id", now=2000)
        assert result["id"] == "new-q-id"
        assert result["source"] == QuestionSource.MANUAL.value
        assert result["review_status"] == QuestionReviewStatus.CONFIRMED.value
        assert result["stem"] == "新增题目"
        assert result["created_at"] == 2000
        assert result["updated_at"] == 2000

    def test_create_manual_multiple_choice(self):
        module = QuestionReviewModule()
        request = CreateQuestionRequest(
            type=QuestionType.MULTIPLE_CHOICE,
            stem="多选",
            options=["X", "Y", "Z"],
            answers={0, 2},
            knowledge_points=["KP2"],
            highlight_source_ids=[],
        )
        result = module.create_manual(request, "new-q-2", now=3000)
        assert result["source"] == QuestionSource.MANUAL.value
        assert result["type"] == QuestionType.MULTIPLE_CHOICE.value
        assert result["answers"] == [0, 2]


class TestUpdate:
    def test_update_preserves_source_and_status(self):
        module = QuestionReviewModule()
        stored = _stored(
            source=QuestionSource.CANDIDATE.value,
            review_status=QuestionReviewStatus.CANDIDATE.value,
        )
        request = UpdateQuestionRequest(
            type=QuestionType.MULTIPLE_CHOICE,
            stem="更新后题目",
            options=["新A", "新B"],
            answers={1},
            knowledge_points=["新KP"],
            highlight_source_ids=[],
        )
        result = module.update(stored, request, now=4000)
        assert result["source"] == QuestionSource.CANDIDATE.value  # 保持来源
        assert result["review_status"] == QuestionReviewStatus.CANDIDATE.value  # 保持状态
        assert result["stem"] == "更新后题目"
        assert result["updated_at"] == 4000

    def test_update_all_fields(self):
        module = QuestionReviewModule()
        stored = _stored()
        request = UpdateQuestionRequest(
            type=QuestionType.SINGLE_CHOICE,
            stem="完整更新",
            options=["选项1", "选项2"],
            answers={0},
            knowledge_points=["新知识点1", "新知识点2"],
            highlight_source_ids=["h-new"],
            hint="新提示",
            explanation="新解析",
        )
        result = module.update(stored, request, now=5000)
        assert result["stem"] == "完整更新"
        assert result["knowledge_points"] == ["新知识点1", "新知识点2"]
        assert result["highlight_source_ids"] == ["h-new"]
        assert result["hint"] == "新提示"
        assert result["explanation"] == "新解析"
        assert result["updated_at"] == 5000


class TestConfirm:
    def test_confirm_candidate_success(self):
        module = QuestionReviewModule()
        stored = _stored(
            source=QuestionSource.CANDIDATE.value,
            review_status=QuestionReviewStatus.CANDIDATE.value,
        )
        result = module.confirm(stored, now=6000)
        assert result["review_status"] == QuestionReviewStatus.CONFIRMED.value
        assert result["updated_at"] == 6000

    def test_confirm_already_confirmed_raises(self):
        module = QuestionReviewModule()
        stored = _stored(
            source=QuestionSource.CANDIDATE.value,
            review_status=QuestionReviewStatus.CONFIRMED.value,
        )
        try:
            module.confirm(stored, now=7000)
            assert False, "应抛出异常"
        except Exception as e:
            assert "已经确认" in str(e)

    def test_confirm_manual_source_raises(self):
        module = QuestionReviewModule()
        stored = _stored(
            source=QuestionSource.MANUAL.value,
            review_status=QuestionReviewStatus.CONFIRMED.value,
        )
        try:
            module.confirm(stored, now=8000)
            assert False, "应抛出异常"
        except Exception as e:
            assert "候选题" in str(e)


class TestIsPublishUnlocked:
    def test_no_candidates_one_manual_unlocked(self):
        """只有手工题，确认后解锁。"""
        module = QuestionReviewModule()
        questions = [
            _stored(
                source=QuestionSource.MANUAL.value,
                review_status=QuestionReviewStatus.CONFIRMED.value,
            ),
        ]
        assert module.is_publish_unlocked(questions) is True

    def test_no_questions_locked(self):
        """没有任何题目时锁定。"""
        module = QuestionReviewModule()
        assert module.is_publish_unlocked([]) is False

    def test_unconfirmed_candidates_locked(self):
        """有未确认的候选题时锁定。"""
        module = QuestionReviewModule()
        questions = [
            _stored(
                source=QuestionSource.CANDIDATE.value,
                review_status=QuestionReviewStatus.CANDIDATE.value,
            ),
        ]
        assert module.is_publish_unlocked(questions) is False

    def test_all_candidates_confirmed_unlocked(self):
        """所有候选题确认后解锁。"""
        module = QuestionReviewModule()
        questions = [
            _stored(
                id="c1",
                source=QuestionSource.CANDIDATE.value,
                review_status=QuestionReviewStatus.CONFIRMED.value,
            ),
            _stored(
                id="c2",
                source=QuestionSource.CANDIDATE.value,
                review_status=QuestionReviewStatus.CONFIRMED.value,
            ),
        ]
        assert module.is_publish_unlocked(questions) is True

    def test_mixed_confirmed_and_unconfirmed_locked(self):
        """部分确认部分未确认时锁定。"""
        module = QuestionReviewModule()
        questions = [
            _stored(
                id="c1",
                source=QuestionSource.CANDIDATE.value,
                review_status=QuestionReviewStatus.CONFIRMED.value,
            ),
            _stored(
                id="c2",
                source=QuestionSource.CANDIDATE.value,
                review_status=QuestionReviewStatus.CANDIDATE.value,
            ),
        ]
        assert module.is_publish_unlocked(questions) is False

    def test_no_candidates_but_has_manual_unlocked(self):
        """没有候选题但有手工题时解锁。"""
        module = QuestionReviewModule()
        questions = [
            _stored(
                source=QuestionSource.MANUAL.value,
                review_status=QuestionReviewStatus.CONFIRMED.value,
            ),
        ]
        assert module.is_publish_unlocked(questions) is True
