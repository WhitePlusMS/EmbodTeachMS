"""课堂练习子模块：获取详情与提交作答。

从 PracticeModule 提取为独立的 ClassroomPractice 类。
"""
import json
import logging
import sqlite3
import uuid
from collections.abc import Callable

from app.auth.models import UserView
from app.common.errors import BusinessError
from app.database import Database
from app.teaching_classes.access import TeachingClassAccess
from app.teaching_classes.models import (
    ClassroomPracticeAnswerRequest,
    ClassroomPracticeAttemptView,
    ClassroomPracticeContentDetailView,
    ClassroomPracticeResultView,
    ContentType,
    PublishedContentDetailView,
    PublishedQuestionView,
)
# check_answer_correct, to_published_question 从 practice 延迟导入以避循环依赖

logger = logging.getLogger("course_agent.practice.classroom")


class ClassroomPractice:
    """课堂练习子模块：获取练习详情与提交答案核对。"""

    def __init__(
        self,
        database: Database,
        now_provider: Callable[[], int],
    ) -> None:
        self._database = database
        self._now = now_provider
        self._access = TeachingClassAccess()

    def get_classroom_practice_content_detail(
        self, class_id: str, content_id: str, learner: UserView
    ) -> ClassroomPracticeContentDetailView:
        """获取课堂练习内容详情，包含作答状态"""
        with self._database.connect() as connection:
            # 验证学习者是否为班级正式成员
            self._access.require_membership(
                connection, class_id, learner.id, message="只有正式成员可以查看课堂练习"
            )

            # 获取课程内容详情
            content_row = connection.execute(
                """
                SELECT
                    cc.id, cc.class_id, cc.content_type, cc.publication_status,
                    cc.title, cc.content, cc.due_at, cc.description,
                    cc.created_at, cc.updated_at,
                    cq.question_type, cq.stem, cq.options_json,
                    cq.correct_answers_json, cq.knowledge_points_json,
                    cq.hint, cq.explanation,
                    ps.id as source_preparation_session_id,
                    ps.owner_teacher_id as source_teacher_id,
                    ps.original_filename as source_filename,
                    COALESCE((SELECT json_group_array(json_object(
                        'id', ph.id, 'paragraphOrdinal', ph.segment_ordinal,
                        'startOffset', ph.start_offset, 'endOffset', ph.end_offset,
                        'createdAt', ph.created_at
                    )) FROM preparation_highlights ph WHERE ph.session_id = ps.id), '[]') AS highlights_json
                FROM course_contents cc
                JOIN course_content_questions cq ON cq.content_id = cc.id
                LEFT JOIN preparation_sessions ps ON ps.class_id = cc.class_id
                WHERE cc.id = ? AND cc.class_id = ? AND cc.publication_status = 'published'
                LIMIT 1
                """,
                (content_id, class_id),
            ).fetchone()

            if content_row is None:
                raise BusinessError(
                    status_code=404,
                    code="RESOURCE_NOT_FOUND",
                    message="课堂练习不存在或已删除",
                )

            # 验证内容类型是课堂练习
            if content_row["content_type"] != ContentType.QUESTION.value:
                raise BusinessError(
                    status_code=400,
                    code="INVALID_CONTENT_TYPE",
                    message="该内容不是课堂练习",
                )

            # 获取已有的作答记录
            attempt_row = connection.execute(
                """
                SELECT * FROM classroom_practice_attempts
                WHERE learner_id = ? AND content_id = ?
                """,
                (learner.id, content_id),
            ).fetchone()

            attempt = None
            if attempt_row:
                attempt = ClassroomPracticeAttemptView(
                    id=attempt_row["id"],
                    learner_id=attempt_row["learner_id"],
                    class_id=attempt_row["class_id"],
                    content_id=attempt_row["content_id"],
                    selected_answers=json.loads(attempt_row["selected_answers"]),
                    is_correct=bool(attempt_row["is_correct"]),
                    attempted_at=attempt_row["attempted_at"],
                    created_at=attempt_row["created_at"],
                )

            # 查询当前学习者是否已完成该内容
            completion_row = connection.execute(
                """
                SELECT 1 FROM course_content_completions
                WHERE content_id = ? AND learner_id = ?
                """,
                (content_id, learner.id),
            ).fetchone()

            content_detail = PublishedContentDetailView(
                id=content_row["id"],
                class_id=content_row["class_id"],
                content_type=content_row["content_type"],
                publication_status=content_row["publication_status"],
                title=content_row["title"],
                content=content_row["content"],
                due_at=content_row["due_at"],
                description=content_row["description"],
                created_at=content_row["created_at"],
                updated_at=content_row["updated_at"],
                highlights_json=content_row["highlights_json"] or "[]",
                source_preparation_session_id=content_row["source_preparation_session_id"],
                source_teacher_id=content_row["source_teacher_id"],
                source_filename=content_row["source_filename"],
                completed=completion_row is not None,
                question=self._to_published_question(content_row),
            )

            # 如果已有作答记录，则不允许再次提交
            can_submit = attempt is None
            correct_answers = json.loads(content_row["correct_answers_json"])
            explanation = content_row["explanation"]

            logger.info(
                "classroom_practice_content_detail_fetched class_id=%s content_id=%s learner_id=%s has_attempt=%s",
                class_id,
                content_id,
                learner.id,
                attempt is not None,
            )

            return ClassroomPracticeContentDetailView(
                content=content_detail,
                attempt=attempt,
                can_submit=can_submit,
                correct_answers=correct_answers if attempt is not None else [],
                explanation=explanation if attempt is not None else "",
            )

    def submit_classroom_practice_answer(
        self, request: ClassroomPracticeAnswerRequest, learner: UserView
    ) -> ClassroomPracticeResultView:
        """提交课堂练习答案并核对"""
        now = self._now()
        attempt_id = str(uuid.uuid4())

        with self._database.connect() as connection:
            # 验证学习者是否为班级正式成员
            self._access.require_membership(
                connection, request.class_id, learner.id, message="只有正式成员可以作答课堂练习"
            )

            # 验证课堂练习存在且已发布
            content_row = connection.execute(
                """
                SELECT cc.content_type, cq.options_json, cq.correct_answers_json, cq.explanation
                FROM course_contents cc
                JOIN course_content_questions cq ON cq.content_id = cc.id
                WHERE cc.id = ? AND cc.class_id = ? AND cc.publication_status = 'published'
                """,
                (request.content_id, request.class_id),
            ).fetchone()

            if content_row is None:
                raise BusinessError(
                    status_code=404,
                    code="CONTENT_NOT_FOUND",
                    message="课堂练习不存在或未发布",
                )

            # 验证内容类型是课堂练习
            if content_row["content_type"] != ContentType.QUESTION.value:
                raise BusinessError(
                    status_code=400,
                    code="INVALID_CONTENT_TYPE",
                    message="该内容不是课堂练习",
                )

            if not request.selected_answers:
                raise BusinessError(
                    status_code=400,
                    code="NO_ANSWER_SELECTED",
                    message="请选择答案后再核对",
                )

            # 检查是否已存在作答记录
            existing_attempt = connection.execute(
                """
                SELECT id FROM classroom_practice_attempts
                WHERE learner_id = ? AND content_id = ?
                """,
                (learner.id, request.content_id),
            ).fetchone()

            if existing_attempt:
                raise BusinessError(
                    status_code=400,
                    code="ATTEMPT_ALREADY_EXISTS",
                    message="您已经作答过这道题目",
                )

            correct_answers = json.loads(content_row["correct_answers_json"])
            explanation = content_row["explanation"]

            # 验证提交的答案索引是否在合理范围内
            option_count = len(json.loads(content_row["options_json"]))
            if any(answer >= option_count for answer in request.selected_answers):
                raise BusinessError(
                    status_code=400,
                    code="INVALID_ANSWER_INDEX",
                    message="答案索引超出选项范围",
                )

            # 核对答案
            is_correct = self._check_answer_correct(request.selected_answers, correct_answers)

            # 保存作答记录（唯一约束 UNIQUE(learner_id, content_id) 兜底并发竞态）
            insert_result = connection.execute(
                """
                INSERT OR IGNORE INTO classroom_practice_attempts (
                    id, learner_id, class_id, content_id, selected_answers, is_correct, attempted_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    attempt_id,
                    learner.id,
                    request.class_id,
                    request.content_id,
                    json.dumps(request.selected_answers, separators=(",", ":")),
                    is_correct,
                    now,
                    now,
                ),
            )
            if insert_result.rowcount != 1:
                raise BusinessError(
                    status_code=400,
                    code="ATTEMPT_ALREADY_EXISTS",
                    message="您已经作答过这道题目",
                )

            # 课堂练习提交即完成：作答记录与完成记录在同一事务中写入，
            # 避免出现“已经提交但课程进度仍未完成”的中间状态。
            completion_id = str(uuid.uuid4())
            connection.execute(
                """
                INSERT OR IGNORE INTO course_content_completions (
                    id, learner_id, class_id, content_id, completed_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (completion_id, learner.id, request.class_id, request.content_id, now, now),
            )

            # 获取保存的作答记录
            attempt_row = connection.execute(
                """
                SELECT * FROM classroom_practice_attempts WHERE id = ?
                """,
                (attempt_id,),
            ).fetchone()

            attempt = ClassroomPracticeAttemptView(
                id=attempt_row["id"],
                learner_id=attempt_row["learner_id"],
                class_id=attempt_row["class_id"],
                content_id=attempt_row["content_id"],
                selected_answers=json.loads(attempt_row["selected_answers"]),
                is_correct=bool(attempt_row["is_correct"]),
                attempted_at=attempt_row["attempted_at"],
                created_at=attempt_row["created_at"],
            )

            logger.info(
                "classroom_practice_answer_submitted learner_id=%s class_id=%s content_id=%s is_correct=%s completed=true",
                learner.id,
                request.class_id,
                request.content_id,
                is_correct,
            )

            return ClassroomPracticeResultView(
                is_correct=is_correct,
                correct_answers=correct_answers,
                explanation=explanation,
                attempt=attempt,
            )

    @staticmethod
    def _to_published_question(row: sqlite3.Row) -> PublishedQuestionView | None:
        """从联表结果构造不含答案的学习者题目视图。"""
        if "question_type" not in row.keys() or row["question_type"] is None:
            return None
        return PublishedQuestionView(
            type=row["question_type"],
            stem=row["stem"],
            options=json.loads(row["options_json"]),
            knowledge_points=json.loads(row["knowledge_points_json"]),
            hint=row["hint"],
        )

    @staticmethod
    def _check_answer_correct(selected_answers: list[int], correct_answers: list[int]) -> bool:
        """核对答案是否正确"""
        if not selected_answers:
            return False
        return set(selected_answers) == set(correct_answers)
