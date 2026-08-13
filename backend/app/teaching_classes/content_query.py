"""已发布课程内容查询模块：内容列表、详情和完成标记。

从 TeachingClassService 提取的独立模块。
"""
from __future__ import annotations

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
    CourseContentCompletionView,
    CourseHomeSummaryView,
    MarkContentCompleteRequest,
    PublishedContentView,
    PublishedContentDetailView,
    PublishedContentListView,
    TeacherPublishedContentListView,
    TeacherPublishedContentView,
    TeacherPublishedQuestionView,
    MasterySummaryView,
    UpdatePublishedContentRequest,
)
from app.teaching_classes.practice import PracticeModule, to_published_question


logger = logging.getLogger("course_agent.teaching_classes.content_query")


class PublishedContentQuery:
    """已发布课程内容查询：内容列表、详情、完成标记、课程首页摘要。"""

    def __init__(
        self,
        database: Database,
        now_provider: Callable[[], int],
        practice: PracticeModule,
    ) -> None:
        self._database = database
        self._now = now_provider
        self._access = TeachingClassAccess()
        self._practice = practice

    @staticmethod
    def _to_teacher_published_question(row: sqlite3.Row) -> TeacherPublishedQuestionView | None:
        if row["question_type"] is None:
            return None
        return TeacherPublishedQuestionView(
            type=row["question_type"], stem=row["stem"],
            options=json.loads(row["options_json"]),
            knowledge_points=json.loads(row["knowledge_points_json"]),
            hint=row["hint"], answers=json.loads(row["correct_answers_json"]),
            explanation=row["explanation"],
        )

    @staticmethod
    def _teacher_content_from_row(row: sqlite3.Row) -> TeacherPublishedContentView:
        """将教师内容查询行转换为统一教师 DTO。"""
        return TeacherPublishedContentView(
            id=row["id"], class_id=row["class_id"],
            content_type=row["content_type"],
            publication_status=row["publication_status"],
            title=row["title"], content=row["content"],
            due_at=row["due_at"], description=row["description"],
            created_at=row["created_at"], updated_at=row["updated_at"],
            question=PublishedContentQuery._to_teacher_published_question(row),
        )

    @staticmethod
    def _find_teacher_content(
        connection: sqlite3.Connection,
        class_id: str,
        content_id: str,
    ) -> sqlite3.Row:
        row = connection.execute(
            """
            SELECT cc.id, cc.class_id, cc.content_type, cc.publication_status,
                   cc.title, cc.content, cc.due_at, cc.description,
                   cc.created_at, cc.updated_at,
                   cq.question_type, cq.stem, cq.options_json,
                   cq.correct_answers_json, cq.knowledge_points_json,
                   cq.hint, cq.explanation
            FROM course_contents cc
            LEFT JOIN course_content_questions cq ON cq.content_id = cc.id
            WHERE cc.id = ? AND cc.class_id = ? AND cc.publication_status = 'published'
            LIMIT 1
            """,
            (content_id, class_id),
        ).fetchone()
        if row is None:
            raise BusinessError(
                status_code=404,
                code="PUBLISHED_CONTENT_NOT_FOUND",
                message="课程内容不存在或已删除",
            )
        return row

    # ── 教师内容列表 ──────────────────────────────────────────────

    def list_published_contents(self, class_id: str, teacher: UserView) -> TeacherPublishedContentListView:
        with self._database.connect() as connection:
            self._access.require_owned_class(connection, class_id, teacher)
            rows = connection.execute(
                """SELECT cc.id, cc.class_id, cc.content_type, cc.publication_status,
                          cc.title, cc.content, cc.due_at, cc.description,
                          cc.created_at, cc.updated_at,
                          cq.question_type, cq.stem, cq.options_json,
                          cq.correct_answers_json, cq.knowledge_points_json,
                          cq.hint, cq.explanation
                   FROM course_contents cc
                   LEFT JOIN course_content_questions cq ON cq.content_id = cc.id
                   WHERE cc.class_id = ? AND cc.publication_status = 'published'
                   ORDER BY cc.created_at DESC""",
                (class_id,),
            ).fetchall()
            items = [self._teacher_content_from_row(row) for row in rows]
        logger.info("published_contents_listed class_id=%s teacher_id=%s count=%d", class_id, teacher.id, len(items))
        return TeacherPublishedContentListView(items=items)

    def update_published_content(
        self,
        class_id: str,
        content_id: str,
        request: UpdatePublishedContentRequest,
        teacher: UserView,
    ) -> TeacherPublishedContentView:
        """教师修改已发布课堂练习或作业。"""
        now = self._now()
        with self._database.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._access.require_owned_class(connection, class_id, teacher)
            row = self._find_teacher_content(connection, class_id, content_id)
            if row["content_type"] not in {"question", "homework"}:
                raise BusinessError(
                    status_code=400,
                    code="CONTENT_TYPE_NOT_EDITABLE",
                    message="当前课程内容类型不支持编辑",
                )

            title = request.title.strip()
            if row["content_type"] == "homework":
                due_at = request.due_at if request.due_at is not None else row["due_at"]
                if due_at is None or due_at <= now:
                    raise BusinessError(
                        status_code=400,
                        code="HOMEWORK_DUE_AT_INVALID",
                        message="作业截止时间必须大于当前时间",
                    )
                description = request.description if request.description is not None else row["description"] or ""
                content = f"作业标题: {title}"
                if description:
                    content += f"\n\n作业描述: {description}"
                content += f"\n\n截止时间: {due_at}"
                connection.execute(
                    """
                    UPDATE course_contents
                    SET title = ?, content = ?, due_at = ?, description = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (title, content, due_at, description, now, content_id),
                )
            else:
                question_row = connection.execute(
                    """
                    SELECT question_type, stem, options_json, correct_answers_json,
                           knowledge_points_json, hint, explanation
                    FROM course_content_questions WHERE content_id = ?
                    """,
                    (content_id,),
                ).fetchone()
                if question_row is None:
                    raise BusinessError(
                        status_code=409,
                        code="QUESTION_CONTENT_INVALID",
                        message="题目内容结构不完整，无法编辑",
                    )
                stem = request.stem if request.stem is not None else question_row["stem"]
                options = request.options if request.options is not None else json.loads(question_row["options_json"])
                answers = request.answers if request.answers is not None else json.loads(question_row["correct_answers_json"])
                knowledge_points = request.knowledge_points if request.knowledge_points is not None else json.loads(question_row["knowledge_points_json"])
                self._validate_question_values(question_row["question_type"], options, answers, knowledge_points)
                hint = request.hint if request.hint is not None else question_row["hint"]
                explanation = request.explanation if request.explanation is not None else question_row["explanation"]
                connection.execute(
                    "UPDATE course_contents SET title = ?, content = ?, updated_at = ? WHERE id = ?",
                    (title, stem, now, content_id),
                )
                connection.execute(
                    """
                    UPDATE course_content_questions
                    SET stem = ?, options_json = ?, correct_answers_json = ?,
                        knowledge_points_json = ?, hint = ?, explanation = ?
                    WHERE content_id = ?
                    """,
                    (
                        stem,
                        json.dumps(options, ensure_ascii=False, separators=(",", ":")),
                        json.dumps(sorted(answers), separators=(",", ":")),
                        json.dumps(knowledge_points, ensure_ascii=False, separators=(",", ":")),
                        hint,
                        explanation,
                        content_id,
                    ),
                )

            updated = self._find_teacher_content(connection, class_id, content_id)
        logger.info("published_content_updated class_id=%s content_id=%s teacher_id=%s", class_id, content_id, teacher.id)
        return self._teacher_content_from_row(updated)

    @staticmethod
    def _validate_question_values(
        question_type: str,
        options: list[str],
        answers: list[int],
        knowledge_points: list[str],
    ) -> None:
        """校验教师修改后的结构化题目。"""
        normalized_options = [option.strip() for option in options]
        if not normalized_options or any(not option for option in normalized_options):
            raise BusinessError(status_code=400, code="QUESTION_OPTIONS_INVALID", message="题目选项不能为空")
        if len(normalized_options) != len(set(normalized_options)):
            raise BusinessError(status_code=400, code="QUESTION_OPTIONS_INVALID", message="题目选项不能重复")
        if not answers or any(answer < 0 or answer >= len(normalized_options) for answer in answers):
            raise BusinessError(status_code=400, code="QUESTION_ANSWERS_INVALID", message="题目答案无效")
        if question_type == "single_choice" and len(answers) != 1:
            raise BusinessError(status_code=400, code="QUESTION_ANSWERS_INVALID", message="单选题只能有一个答案")
        if question_type == "multiple_choice" and len(set(answers)) != len(answers):
            raise BusinessError(status_code=400, code="QUESTION_ANSWERS_INVALID", message="多选题答案不能重复")
        if not knowledge_points or any(not point.strip() for point in knowledge_points):
            raise BusinessError(status_code=400, code="QUESTION_KNOWLEDGE_POINTS_INVALID", message="至少填写一个知识点")

    def delete_published_content(
        self,
        class_id: str,
        content_id: str,
        teacher: UserView,
    ) -> None:
        """教师删除已发布课堂练习或作业及其关联事实。"""
        with self._database.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._access.require_owned_class(connection, class_id, teacher)
            row = self._find_teacher_content(connection, class_id, content_id)
            if row["content_type"] not in {"question", "homework"}:
                raise BusinessError(
                    status_code=400,
                    code="CONTENT_TYPE_NOT_DELETABLE",
                    message="当前课程内容类型不支持删除",
                )
            question_ids: list[str] = []
            if row["content_type"] == "homework":
                question_ids = [
                    item["question_id"]
                    for item in connection.execute(
                        "SELECT question_id FROM homework_questions WHERE homework_id = ?",
                        (content_id,),
                    ).fetchall()
                ]
                for question_id in question_ids:
                    has_other_homework = connection.execute(
                        "SELECT 1 FROM homework_questions WHERE question_id = ? AND homework_id <> ? LIMIT 1",
                        (question_id, content_id),
                    ).fetchone()
                    if has_other_homework is None:
                        connection.execute("DELETE FROM course_contents WHERE id = ?", (question_id,))
            connection.execute("DELETE FROM course_contents WHERE id = ?", (content_id,))
        logger.info("published_content_deleted class_id=%s content_id=%s teacher_id=%s", class_id, content_id, teacher.id)

    # ── 学习者内容列表/详情 ───────────────────────────────────────

    def list_published_contents_for_learner(self, class_id: str, learner: UserView) -> PublishedContentListView:
        with self._database.connect() as connection:
            self._access.require_membership(connection, class_id, learner.id, message="只有正式成员可以查看课程内容")
            rows = connection.execute(
                """SELECT course_contents.id, course_contents.class_id,
                          course_contents.content_type, course_contents.publication_status,
                          course_contents.title, course_contents.content,
                          course_contents.due_at, course_contents.description,
                          course_contents.created_at, course_contents.updated_at,
                          ccc.id AS completion_id
                   FROM course_contents
                   LEFT JOIN course_content_completions ccc
                     ON ccc.content_id = course_contents.id AND ccc.learner_id = ?
                   WHERE course_contents.class_id = ?
                     AND course_contents.publication_status = 'published'
                     AND NOT EXISTS (
                         SELECT 1 FROM homework_questions hq
                         WHERE hq.question_id = course_contents.id
                     )
                   ORDER BY course_contents.created_at ASC""",
                (learner.id, class_id),
            ).fetchall()
            items = [
                PublishedContentView(
                    id=row["id"], class_id=row["class_id"],
                    content_type=row["content_type"],
                    publication_status=row["publication_status"],
                    title=row["title"], content=row["content"],
                    due_at=row["due_at"], description=row["description"],
                    created_at=row["created_at"], updated_at=row["updated_at"],
                    completed=row["completion_id"] is not None,
                )
                for row in rows
            ]
        logger.info(
            "published_contents_listed_for_learner class_id=%s learner_id=%s count=%d",
            class_id,
            learner.id,
            len(items),
        )
        return PublishedContentListView(items=items)

    def get_published_content_detail_for_learner(
        self, class_id: str, content_id: str, learner: UserView
    ) -> PublishedContentDetailView:
        with self._database.connect() as connection:
            self._access.require_membership(connection, class_id, learner.id, message="只有正式成员可以查看课程内容")
            row = connection.execute(
                """SELECT cc.id, cc.class_id, cc.content_type, cc.publication_status,
                          cc.title, cc.content, cc.due_at, cc.description,
                          cc.created_at, cc.updated_at,
                          cq.question_type, cq.stem, cq.options_json,
                          cq.knowledge_points_json, cq.hint,
                          ps.id as source_preparation_session_id,
                          ps.owner_teacher_id as source_teacher_id,
                          ps.original_filename as source_filename,
                          COALESCE((SELECT json_group_array(json_object(
                              'id', cch.id, 'paragraphOrdinal', cch.paragraph_ordinal,
                              'startOffset', cch.start_offset, 'endOffset', cch.end_offset,
                              'createdAt', cch.created_at
                          )) FROM course_content_highlights cch
                           WHERE cch.content_id = cc.id), '[]') AS highlights_json,
                          ccc.id as completion_id
                   FROM course_contents cc
                   LEFT JOIN course_content_questions cq ON cq.content_id = cc.id
                   LEFT JOIN preparation_sessions ps ON ps.class_id = cc.class_id
                   LEFT JOIN course_content_completions ccc ON ccc.content_id = cc.id AND ccc.learner_id = ?
                   WHERE cc.id = ? AND cc.class_id = ? AND cc.publication_status = 'published'
                   LIMIT 1""",
                (learner.id, content_id, class_id),
            ).fetchone()
            if row is None:
                raise BusinessError(status_code=404, code="RESOURCE_NOT_FOUND", message="课程内容不存在或已删除")
        logger.info("published_content_detail_fetched class_id=%s content_id=%s learner_id=%s", class_id, content_id, learner.id)
        return PublishedContentDetailView(
            id=row["id"], class_id=row["class_id"], content_type=row["content_type"],
            publication_status=row["publication_status"], title=row["title"],
            content=row["content"], due_at=row["due_at"], description=row["description"],
            created_at=row["created_at"], updated_at=row["updated_at"],
            highlights_json=row["highlights_json"] or "[]",
            source_preparation_session_id=row["source_preparation_session_id"],
            source_teacher_id=row["source_teacher_id"],
            source_filename=row["source_filename"],
            question=to_published_question(row),
            completed=row["completion_id"] is not None,
        )

    # ── 完成标记 ──────────────────────────────────────────────────

    def mark_content_complete(self, request: MarkContentCompleteRequest, learner: UserView) -> CourseContentCompletionView:
        now = self._now()
        completion_id = str(uuid.uuid4())
        with self._database.connect() as connection:
            self._access.require_membership(connection, request.class_id, learner.id, message="只有正式成员可以标记内容完成")
            content = connection.execute(
                "SELECT id, content_type FROM course_contents WHERE id = ? AND class_id = ? AND publication_status = 'published'",
                (request.content_id, request.class_id),
            ).fetchone()
            if not content:
                raise BusinessError(status_code=404, code="CONTENT_NOT_FOUND", message="课程内容不存在或未发布")
            if content["content_type"] in {"homework", "question"}:
                completion_kind = "作业" if content["content_type"] == "homework" else "课堂练习"
                error_code = (
                    "HOMEWORK_COMPLETION_REQUIRES_SUBMISSION"
                    if content["content_type"] == "homework"
                    else "CLASSROOM_PRACTICE_COMPLETION_REQUIRES_SUBMISSION"
                )
                raise BusinessError(
                    status_code=400,
                    code=error_code,
                    message=f"{completion_kind}必须正式提交后自动完成，不能手动标记完成",
                )
            existing = connection.execute(
                "SELECT id FROM course_content_completions WHERE learner_id = ? AND class_id = ? AND content_id = ?",
                (learner.id, request.class_id, request.content_id),
            ).fetchone()
            if existing:
                row = connection.execute(
                    "SELECT * FROM course_content_completions WHERE id = ?", (existing["id"],)
                ).fetchone()
                return CourseContentCompletionView(
                    id=row["id"], learner_id=row["learner_id"], class_id=row["class_id"],
                    content_id=row["content_id"], completed_at=row["completed_at"],
                    created_at=row["created_at"],
                )
            insert_result = connection.execute(
                "INSERT OR IGNORE INTO course_content_completions (id, learner_id, class_id, content_id, completed_at, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (completion_id, learner.id, request.class_id, request.content_id, now, now),
            )
            if insert_result.rowcount == 1:
                row = connection.execute("SELECT * FROM course_content_completions WHERE id = ?", (completion_id,)).fetchone()
            else:
                row = connection.execute(
                    "SELECT * FROM course_content_completions WHERE learner_id = ? AND class_id = ? AND content_id = ?",
                    (learner.id, request.class_id, request.content_id),
                ).fetchone()
        logger.info("content_marked_complete learner_id=%s class_id=%s content_id=%s completion_id=%s", learner.id, request.class_id, request.content_id, completion_id)
        return CourseContentCompletionView(
            id=row["id"], learner_id=row["learner_id"], class_id=row["class_id"],
            content_id=row["content_id"], completed_at=row["completed_at"], created_at=row["created_at"],
        )

    # ── 课程首页摘要 ──────────────────────────────────────────────

    def get_course_home_summary(self, class_id: str, learner: UserView) -> CourseHomeSummaryView:
        with self._database.connect() as connection:
            self._access.require_membership(connection, class_id, learner.id, message="只有正式成员可以查看课程首页汇总")
            content_rows = connection.execute(
                """SELECT course_contents.id, course_contents.class_id,
                          course_contents.content_type, course_contents.publication_status,
                          course_contents.title, course_contents.content,
                          course_contents.due_at, course_contents.description,
                          course_contents.created_at, course_contents.updated_at,
                          ccc.id AS completion_id
                   FROM course_contents
                   LEFT JOIN course_content_completions ccc
                     ON ccc.content_id = course_contents.id AND ccc.learner_id = ?
                   WHERE course_contents.class_id = ?
                     AND course_contents.publication_status = 'published'
                     AND NOT EXISTS (
                         SELECT 1 FROM homework_questions hq
                         WHERE hq.question_id = course_contents.id
                     )
                   ORDER BY course_contents.created_at ASC""",
                (learner.id, class_id),
            ).fetchall()
            completion_rows = connection.execute(
                "SELECT content_id FROM course_content_completions WHERE learner_id = ? AND class_id = ?",
                (learner.id, class_id),
            ).fetchall()
            completed_content_ids = {row["content_id"] for row in completion_rows}

            content_list = [
                PublishedContentView(
                    id=row["id"], class_id=row["class_id"],
                    content_type=row["content_type"],
                    publication_status=row["publication_status"],
                    title=row["title"], content=row["content"],
                    due_at=row["due_at"], description=row["description"],
                    created_at=row["created_at"], updated_at=row["updated_at"],
                    completed=row["completion_id"] is not None,
                )
                for row in content_rows
            ]

            total_contents = len(content_list)
            completed_contents = sum(1 for c in content_list if c.id in completed_content_ids)
            completion_rate = round(completed_contents / total_contents, 2) if total_contents > 0 else 0.0
            next_content = next((c for c in content_list if c.id not in completed_content_ids), None)
            pending_homework = [c for c in content_list if c.content_type == "homework" and c.id not in completed_content_ids]

            try:
                mastery_summary = self._practice.get_mastery_summary(class_id, learner)
            except Exception as e:
                logger.error("mastery_summary_error_in_home class_id=%s learner_id=%s error=%s", class_id, learner.id, str(e))
                mastery_summary = MasterySummaryView(
                    status="error", message="掌握度分析暂时不可用",
                    total_knowledge_points=0,
                    level_distribution={"unlearned": 0, "consolidating": 0, "basic_mastery": 0, "proficient_mastery": 0},
                    knowledge_points=[],
                )

            try:
                next_suggestion = self._practice.get_next_suggestion(class_id, learner)
            except Exception as e:
                logger.error("next_suggestion_error_in_home class_id=%s learner_id=%s error=%s", class_id, learner.id, str(e))
                if total_contents == 0:
                    next_suggestion = "教师尚未发布任何课程内容"
                elif next_content:
                    next_suggestion = f"继续学习：{next_content.title}"
                elif pending_homework:
                    next_suggestion = f"完成作业：{pending_homework[0].title}"
                elif total_contents > 0:
                    next_suggestion = "恭喜！您已完成所有课程内容"
                else:
                    next_suggestion = "继续学习课程内容"

        return CourseHomeSummaryView(
            next_content=next_content, content_list=content_list,
            completion_stats={
                "total_contents": total_contents,
                "completed_contents": completed_contents,
                "completion_rate": completion_rate,
            },
            pending_homework=pending_homework,
            next_suggestions=[next_suggestion],
            mastery_summary=mastery_summary,
        )
