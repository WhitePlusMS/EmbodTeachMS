"""作业模块 Facade：组合 HomeworkGrading 判分子模块与 HomeworkStats 统计子模块。

作为作业领域的窄接口 Facade，对外暴露与之前一致的 public 方法：
- save_homework_draft           — 保存作业草稿
- submit_homework               — 提交作业并自动判分
- get_homework_submission_detail — 获取作业提交详情
- list_homework_for_learner      — 学习者获取作业列表
- list_teacher_homework          — 教师获取作业统计列表

内部委托 HomeworkGrading 处理题目加载/验证/判分，
委托 HomeworkStats 处理教师端统计与作业内容查询。
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
from app.teaching_classes.homework_grading import HomeworkGrading
from app.teaching_classes.homework_stats import HomeworkStats
from app.teaching_classes.models import (
    HomeworkListView,
    HomeworkQuestionPreviewView,
    HomeworkQuestionResultView,
    HomeworkSubmissionDetailView,
    HomeworkSubmissionResultView,
    HomeworkSubmissionStatus,
    HomeworkSubmissionView,
    PublishedContentView,
    SaveHomeworkDraftRequest,
    SubmitHomeworkRequest,
    TeacherHomeworkListView,
)

logger = logging.getLogger("course_agent.homework")


class HomeworkModule:
    """作业模块 Facade：学习者作业草稿/提交/判分与教师作业判分统计。

    本模块作为窄 Facade，不直接包含判分或统计逻辑，全部委托给：
    - self._grading: HomeworkGrading  — 题目加载、答案校验、自动判分
    - self._stats: HomeworkStats      — 教师统计、作业内容查询
    """

    def __init__(
        self,
        database: Database,
        now_provider: Callable[[], int],
    ) -> None:
        self._database = database
        self._now = now_provider
        self._access = TeachingClassAccess()
        self._grading = HomeworkGrading()
        self._stats = HomeworkStats()

    def save_homework_draft(
        self, request: SaveHomeworkDraftRequest, learner: UserView
    ) -> HomeworkSubmissionView:
        """保存作业草稿"""
        now = self._now()

        with self._database.connect() as connection:
            # 验证学习者是否为班级正式成员
            self._access.require_membership(
                connection, request.class_id, learner.id, message="只有正式成员可以保存作业草稿"
            )

            # 验证作业存在且已发布
            homework_row = connection.execute(
                """
                SELECT id, due_at FROM course_contents
                WHERE id = ? AND class_id = ? AND content_type = 'homework' AND publication_status = 'published'
                """,
                (request.homework_id, request.class_id),
            ).fetchone()

            if not homework_row:
                raise BusinessError(
                    status_code=404,
                    code="HOMEWORK_NOT_FOUND",
                    message="作业不存在或未发布",
                )

            # 检查是否已有提交记录
            submission_row = connection.execute(
                """
                SELECT id, status FROM homework_submissions
                WHERE learner_id = ? AND homework_id = ?
                """,
                (learner.id, request.homework_id),
            ).fetchone()

            if submission_row and submission_row["status"] == HomeworkSubmissionStatus.SUBMITTED.value:
                raise BusinessError(
                    status_code=400,
                    code="HOMEWORK_ALREADY_SUBMITTED",
                    message="作业已提交，不能修改草稿",
                )

            # 验证答案格式并获取作业题目
            questions = self._grading.get_questions(connection, request.homework_id)
            self._grading.validate_answers(request.answers, questions)

            if submission_row:
                # 更新现有草稿
                update_cursor = connection.execute(
                    """
                    UPDATE homework_submissions
                    SET answers_json = ?, draft_saved_at = ?, updated_at = ?
                    WHERE id = ? AND status = 'draft'
                    """,
                    (
                        json.dumps(request.answers, separators=(",", ":")),
                        now,
                        now,
                        submission_row["id"],
                    ),
                )
                if update_cursor.rowcount != 1:
                    raise BusinessError(
                        status_code=400,
                        code="HOMEWORK_ALREADY_SUBMITTED",
                        message="作业已提交，不能修改草稿",
                    )
                submission_id = submission_row["id"]
            else:
                # 创建新草稿
                submission_id = str(uuid.uuid4())
                try:
                    connection.execute(
                        """
                        INSERT INTO homework_submissions (
                            id, learner_id, class_id, homework_id, status,
                            answers_json, draft_saved_at, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            submission_id,
                            learner.id,
                            request.class_id,
                            request.homework_id,
                            HomeworkSubmissionStatus.DRAFT.value,
                            json.dumps(request.answers, separators=(",", ":")),
                            now,
                            now,
                            now,
                        ),
                    )
                except sqlite3.IntegrityError as error:
                    raise BusinessError(
                        status_code=400,
                        code="HOMEWORK_ALREADY_SUBMITTED",
                        message="作业已提交，不能修改草稿",
                    ) from error

            # 获取更新后的提交记录
            row = connection.execute(
                """
                SELECT * FROM homework_submissions WHERE id = ?
                """,
                (submission_id,),
            ).fetchone()

            logger.info(
                "homework_draft_saved learner_id=%s homework_id=%s submission_id=%s",
                learner.id,
                request.homework_id,
                submission_id,
            )

            return HomeworkSubmissionView(
                id=row["id"],
                learner_id=row["learner_id"],
                class_id=row["class_id"],
                homework_id=row["homework_id"],
                status=HomeworkSubmissionStatus(row["status"]),
                answers_json=row["answers_json"],
                grading_json=row["grading_json"],
                total_score=row["total_score"],
                correct_count=row["correct_count"],
                draft_saved_at=row["draft_saved_at"],
                submitted_at=row["submitted_at"],
                is_late_submission=bool(row["is_late_submission"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def submit_homework(
        self, request: SubmitHomeworkRequest, learner: UserView
    ) -> HomeworkSubmissionResultView:
        """提交作业"""
        now = self._now()

        with self._database.connect() as connection:
            # 验证学习者是否为班级正式成员
            self._access.require_membership(
                connection, request.class_id, learner.id, message="只有正式成员可以提交作业"
            )

            # 验证作业存在且已发布
            homework_row = connection.execute(
                """
                SELECT id, due_at FROM course_contents
                WHERE id = ? AND class_id = ? AND content_type = 'homework' AND publication_status = 'published'
                """,
                (request.homework_id, request.class_id),
            ).fetchone()

            if not homework_row:
                raise BusinessError(
                    status_code=404,
                    code="HOMEWORK_NOT_FOUND",
                    message="作业不存在或未发布",
                )

            # 检查是否已有提交记录
            submission_row = connection.execute(
                """
                SELECT id, status FROM homework_submissions
                WHERE learner_id = ? AND homework_id = ?
                """,
                (learner.id, request.homework_id),
            ).fetchone()

            if submission_row and submission_row["status"] == HomeworkSubmissionStatus.SUBMITTED.value:
                raise BusinessError(
                    status_code=400,
                    code="HOMEWORK_ALREADY_SUBMITTED",
                    message="作业已提交，不能重复提交",
                )

            # 验证答案格式并获取作业题目
            questions = self._grading.get_questions(connection, request.homework_id)
            self._grading.validate_answers(request.answers, questions)

            # 检查是否迟交
            due_at = homework_row["due_at"]
            is_late_submission = due_at is not None and now > due_at

            # 判分
            grading_result = self._grading.grade(request.answers, questions)

            submission_id = str(uuid.uuid4())
            if submission_row:
                # 更新现有记录为已提交
                update_cursor = connection.execute(
                    """
                    UPDATE homework_submissions
                    SET status = ?, answers_json = ?, grading_json = ?,
                        total_score = ?, correct_count = ?, submitted_at = ?,
                        is_late_submission = ?, updated_at = ?
                    WHERE id = ? AND status = 'draft'
                    """,
                    (
                        HomeworkSubmissionStatus.SUBMITTED.value,
                        json.dumps(request.answers, separators=(",", ":")),
                        json.dumps(grading_result["grading"], separators=(",", ":")),
                        grading_result["total_score"],
                        grading_result["correct_count"],
                        now,
                        is_late_submission,
                        now,
                        submission_row["id"],
                    ),
                )
                if update_cursor.rowcount != 1:
                    raise BusinessError(
                        status_code=400,
                        code="HOMEWORK_ALREADY_SUBMITTED",
                        message="作业已提交，不能重复提交",
                    )
                submission_id = submission_row["id"]
            else:
                # 创建新的提交记录
                try:
                    connection.execute(
                        """
                        INSERT INTO homework_submissions (
                            id, learner_id, class_id, homework_id, status,
                            answers_json, grading_json, total_score, correct_count,
                            submitted_at, is_late_submission, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            submission_id,
                            learner.id,
                            request.class_id,
                            request.homework_id,
                            HomeworkSubmissionStatus.SUBMITTED.value,
                            json.dumps(request.answers, separators=(",", ":")),
                            json.dumps(grading_result["grading"], separators=(",", ":")),
                            grading_result["total_score"],
                            grading_result["correct_count"],
                            now,
                            is_late_submission,
                            now,
                            now,
                        ),
                    )
                except sqlite3.IntegrityError as error:
                    raise BusinessError(
                        status_code=400,
                        code="HOMEWORK_ALREADY_SUBMITTED",
                        message="作业已提交，不能重复提交",
                    ) from error

            # 获取作业内容详情
            homework_content = self._stats.get_homework_content(
                connection, request.homework_id, request.class_id
            )

            # 获取更新后的提交记录
            submission_row = connection.execute(
                """
                SELECT * FROM homework_submissions WHERE id = ?
                """,
                (submission_id,),
            ).fetchone()

            submission = HomeworkSubmissionView(
                id=submission_row["id"],
                learner_id=submission_row["learner_id"],
                class_id=submission_row["class_id"],
                homework_id=submission_row["homework_id"],
                status=HomeworkSubmissionStatus(submission_row["status"]),
                answers_json=submission_row["answers_json"],
                grading_json=submission_row["grading_json"],
                total_score=submission_row["total_score"],
                correct_count=submission_row["correct_count"],
                draft_saved_at=submission_row["draft_saved_at"],
                submitted_at=submission_row["submitted_at"],
                is_late_submission=bool(submission_row["is_late_submission"]),
                created_at=submission_row["created_at"],
                updated_at=submission_row["updated_at"],
            )

            logger.info(
                "homework_submitted learner_id=%s homework_id=%s submission_id=%s score=%d/%d is_late=%s",
                learner.id,
                request.homework_id,
                submission_id,
                grading_result["correct_count"],
                len(questions),
                is_late_submission,
            )

            return HomeworkSubmissionResultView(
                submission=submission,
                homework=homework_content,
                questions=grading_result["questions"],
            )

    def get_homework_submission_detail(
        self, class_id: str, homework_id: str, learner: UserView
    ) -> HomeworkSubmissionDetailView:
        """获取作业提交详情"""
        with self._database.connect() as connection:
            # 验证学习者是否为班级正式成员
            self._access.require_membership(
                connection, class_id, learner.id, message="只有正式成员可以查看作业提交详情"
            )

            # 作业资源必须属于路径中的教学班，不能只校验成员资格后按 ID 读取。
            homework_content = self._stats.get_homework_content(connection, homework_id, class_id)

            # 获取提交记录
            submission_row = connection.execute(
                """
                SELECT * FROM homework_submissions
                WHERE learner_id = ? AND homework_id = ?
                """,
                (learner.id, homework_id),
            ).fetchone()

            # 获取作业题目
            questions = self._grading.get_questions(connection, homework_id)

            submission = None
            if submission_row:
                submission = HomeworkSubmissionView(
                    id=submission_row["id"],
                    learner_id=submission_row["learner_id"],
                    class_id=submission_row["class_id"],
                    homework_id=submission_row["homework_id"],
                    status=HomeworkSubmissionStatus(submission_row["status"]),
                    answers_json=submission_row["answers_json"],
                    grading_json=submission_row["grading_json"],
                    total_score=submission_row["total_score"],
                    correct_count=submission_row["correct_count"],
                    draft_saved_at=submission_row["draft_saved_at"],
                    submitted_at=submission_row["submitted_at"],
                    is_late_submission=bool(submission_row["is_late_submission"]),
                    created_at=submission_row["created_at"],
                    updated_at=submission_row["updated_at"],
                )

            logger.info(
                "homework_submission_detail_fetched learner_id=%s homework_id=%s has_submission=%s",
                learner.id,
                homework_id,
                submission is not None,
            )

            public_questions: list[HomeworkQuestionPreviewView | HomeworkQuestionResultView] = [
                HomeworkQuestionPreviewView(
                    id=question.id,
                    type=question.question_type,
                    stem=question.stem,
                    options=question.options,
                    hint=question.hint,
                )
                for question in questions
            ]
            if submission is not None and submission.status == HomeworkSubmissionStatus.SUBMITTED:
                grading = json.loads(submission.grading_json)
                public_questions = [
                    HomeworkQuestionResultView(
                        id=question.id,
                        type=question.question_type,
                        stem=question.stem,
                        options=question.options,
                        hint=question.hint,
                        user_answers=grading[question.id]["user_answers"],
                        correct_answers=grading[question.id]["correct_answers"],
                        is_correct=grading[question.id]["is_correct"],
                        score=grading[question.id]["score"],
                        explanation=grading[question.id]["explanation"],
                    )
                    for question in questions
                ]

            return HomeworkSubmissionDetailView(
                submission=submission,
                homework=homework_content,
                questions=public_questions,
            )

    def list_homework_for_learner(self, class_id: str, learner: UserView) -> HomeworkListView:
        """学习者获取作业列表"""
        with self._database.connect() as connection:
            # 验证学习者是否为班级正式成员
            self._access.require_membership(
                connection, class_id, learner.id, message="只有正式成员可以查看作业列表"
            )

            # 获取作业列表
            homework_rows = connection.execute(
                """
                SELECT id, class_id, content_type, publication_status, title, content,
                       due_at, description, created_at, updated_at
                FROM course_contents
                WHERE class_id = ? AND content_type = 'homework' AND publication_status = 'published'
                ORDER BY created_at DESC
                """,
                (class_id,),
            ).fetchall()

            # 获取提交记录
            submission_rows = connection.execute(
                """
                SELECT * FROM homework_submissions
                WHERE learner_id = ? AND class_id = ?
                """,
                (learner.id, class_id),
            ).fetchall()

            # 转换作业列表
            homework_items = []
            for row in homework_rows:
                homework_items.append(PublishedContentView(
                    id=row["id"],
                    class_id=row["class_id"],
                    content_type=row["content_type"],
                    publication_status=row["publication_status"],
                    title=row["title"],
                    content=row["content"],
                    due_at=row["due_at"],
                    description=row["description"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                ))

            # 转换提交记录映射
            submissions = {}
            for row in submission_rows:
                submissions[row["homework_id"]] = HomeworkSubmissionView(
                    id=row["id"],
                    learner_id=row["learner_id"],
                    class_id=row["class_id"],
                    homework_id=row["homework_id"],
                    status=HomeworkSubmissionStatus(row["status"]),
                    answers_json=row["answers_json"],
                    grading_json=row["grading_json"],
                    total_score=row["total_score"],
                    correct_count=row["correct_count"],
                    draft_saved_at=row["draft_saved_at"],
                    submitted_at=row["submitted_at"],
                    is_late_submission=bool(row["is_late_submission"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )

            logger.info(
                "homework_list_fetched learner_id=%s class_id=%s count=%d",
                learner.id,
                class_id,
                len(homework_items),
            )

            return HomeworkListView(
                items=homework_items,
                submissions=submissions,
            )

    def list_teacher_homework(
        self, class_id: str, teacher: UserView
    ) -> TeacherHomeworkListView:
        """获取教师当前班已发布作业及确定性判分统计。"""
        with self._database.connect() as connection:
            self._access.require_owned_class(connection, class_id, teacher)

            member_row = connection.execute(
                "SELECT COUNT(*) AS total_learners FROM class_memberships WHERE class_id = ?",
                (class_id,),
            ).fetchone()
            total_learners = int(member_row["total_learners"] if member_row else 0)

            homework_rows = connection.execute(
                """
                SELECT id, class_id, content_type, publication_status, title, content,
                       due_at, description, created_at, updated_at
                FROM course_contents
                WHERE class_id = ?
                  AND content_type = 'homework'
                  AND publication_status = 'published'
                ORDER BY created_at DESC, rowid DESC
                """,
                (class_id,),
            ).fetchall()

            items = [
                self._stats.build_teacher_homework_stats(connection, row, total_learners)
                for row in homework_rows
            ]
            logger.info(
                "teacher_homework_listed class_id=%s teacher_id=%s count=%d",
                class_id,
                teacher.id,
                len(items),
            )
            return TeacherHomeworkListView(items=items, no_data=not items)
