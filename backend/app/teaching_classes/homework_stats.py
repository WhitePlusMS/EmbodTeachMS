"""作业教师统计子模块：班级作业提交统计与题目维度分析。

包含构建教师端作业列表所需的统计数据（提交率、正确率、错题分布等），
不包含学习者端草稿保存、提交或判分逻辑。
"""

from __future__ import annotations

import json
import logging
import sqlite3

from app.common.errors import BusinessError
from app.teaching_classes.models import (
    PublishedContentView,
    TeacherHomeworkQuestionStatsView,
    TeacherHomeworkStatsView,
)


logger = logging.getLogger("course_agent.homework_stats")


class HomeworkStats:
    """作业教师统计子模块：构建提交统计与题目维度分析。

    职责：
    - build_teacher_homework_stats  — 构造单份作业的教师统计视图
    - get_homework_content          — 获取已发布的作业内容详情
    """

    @staticmethod
    def build_teacher_homework_stats(
        connection: sqlite3.Connection,
        homework_row: sqlite3.Row,
        total_learners: int,
    ) -> TeacherHomeworkStatsView:
        """从已提交判分事实构建单份作业统计。"""
        homework_id = homework_row["id"]
        homework = PublishedContentView(
            id=homework_id,
            class_id=homework_row["class_id"],
            content_type=homework_row["content_type"],
            publication_status=homework_row["publication_status"],
            title=homework_row["title"],
            content=homework_row["content"],
            due_at=homework_row["due_at"],
            description=homework_row["description"],
            created_at=homework_row["created_at"],
            updated_at=homework_row["updated_at"],
        )
        question_rows = connection.execute(
            """
            SELECT cc.id, cc.content
            FROM homework_questions hq
            JOIN course_contents cc ON cc.id = hq.question_id
            WHERE hq.homework_id = ?
              AND cc.class_id = ?
              AND cc.publication_status = 'published'
            ORDER BY hq.ordinal ASC, hq.rowid ASC
            """,
            (homework_id, homework_row["class_id"]),
        ).fetchall()
        submission_rows = connection.execute(
            """
            SELECT hs.id, hs.learner_id, hs.grading_json, hs.is_late_submission
            FROM homework_submissions hs
            JOIN class_memberships cm
              ON cm.class_id = hs.class_id
             AND cm.learner_id = hs.learner_id
            WHERE hs.class_id = ?
              AND hs.homework_id = ?
              AND hs.status = 'submitted'
            ORDER BY hs.submitted_at ASC, hs.rowid ASC
            """,
            (homework_row["class_id"], homework_id),
        ).fetchall()

        question_stats: list[TeacherHomeworkQuestionStatsView] = []
        pending_submission_ids: set[str] = set()
        overall_attempts = 0
        overall_correct = 0
        for question_row in question_rows:
            total_attempts = 0
            correct_attempts = 0
            error_counts: dict[str, int] = {}
            for submission_row in submission_rows:
                try:
                    grading = json.loads(submission_row["grading_json"] or "{}")
                except json.JSONDecodeError:
                    pending_submission_ids.add(submission_row["id"])
                    continue
                detail = grading.get(question_row["id"]) if isinstance(grading, dict) else None
                if not isinstance(detail, dict) or "is_correct" not in detail:
                    pending_submission_ids.add(submission_row["id"])
                    continue
                total_attempts += 1
                is_correct = detail["is_correct"] is True
                if is_correct:
                    correct_attempts += 1
                else:
                    user_answers = detail.get("user_answers", [])
                    if isinstance(user_answers, list) and user_answers:
                        error_key = "、".join(
                            f"选项{int(answer) + 1}" for answer in user_answers
                        )
                    else:
                        error_key = "未作答"
                    error_counts[error_key] = error_counts.get(error_key, 0) + 1

            overall_attempts += total_attempts
            overall_correct += correct_attempts
            common_error_reason = None
            if error_counts:
                common_error, error_count = min(
                    error_counts.items(), key=lambda item: (-item[1], item[0])
                )
                common_error_reason = f"{common_error}（{error_count}次）"
            question_stats.append(
                TeacherHomeworkQuestionStatsView(
                    question_id=question_row["id"],
                    question_content=question_row["content"],
                    total_attempts=total_attempts,
                    correct_attempts=correct_attempts,
                    correct_rate=(
                        round(correct_attempts / total_attempts * 100, 2)
                        if total_attempts
                        else None
                    ),
                    common_error_reason=common_error_reason,
                )
            )

        submitted_count = len(submission_rows)
        submitted_learner_ids = [str(row["learner_id"]) for row in submission_rows]
        pending_review_count = len(pending_submission_ids)
        if not submitted_count:
            data_status = "no_submissions"
        elif pending_review_count or not question_stats or not overall_attempts:
            data_status = "insufficient_data"
        else:
            data_status = "ready"
        return TeacherHomeworkStatsView(
            homework=homework,
            total_learners=total_learners,
            submitted_count=submitted_count,
            submitted_learner_ids=submitted_learner_ids,
            late_count=sum(1 for row in submission_rows if row["is_late_submission"]),
            correct_rate=(
                round(overall_correct / overall_attempts * 100, 2)
                if overall_attempts
                else None
            ),
            pending_review_count=pending_review_count,
            data_status=data_status,
            question_stats=question_stats,
        )

    @staticmethod
    def get_homework_content(
        connection: sqlite3.Connection, homework_id: str, class_id: str | None = None
    ) -> PublishedContentView:
        """获取已发布的作业内容。"""
        row = connection.execute(
            """
            SELECT id, class_id, content_type, publication_status, title, content,
                   due_at, description, created_at, updated_at
            FROM course_contents
            WHERE id = ?
              AND (? IS NULL OR class_id = ?)
              AND content_type = 'homework'
              AND publication_status = 'published'
            """,
            (homework_id, class_id, class_id),
        ).fetchone()
        if row is None:
            raise BusinessError(
                status_code=404,
                code="HOMEWORK_NOT_FOUND",
                message="作业不存在或未发布",
            )
        return PublishedContentView(
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
        )
