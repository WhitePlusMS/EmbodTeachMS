import logging
import json
import sqlite3

from app.auth.models import UserRole, UserView
from app.common.errors import BusinessError
from app.database import Database
from app.teaching_classes.access import TeachingClassAccess
from app.teaching_classes.mastery_models import MasteryLevel
from app.teaching_classes.mastery_service import MasteryService
from app.teaching_classes.models import (
    CourseCompletionStatsView,
    LearnerDetailView,
    LearnerListView,
    LearnerPreviewView,
    SimulationSummaryView,
    TeacherDashboardConsolidationView,
    TeacherDashboardHomeworkSummaryView,
    TeacherDashboardLearnerPreviewView,
    TeacherDashboardView,
)
from app.teaching_classes.practice import PracticeModule

logger = logging.getLogger("course_agent.teacher_insight")


class TeacherInsightModule:
    """教师教学分析模块：教师仪表盘、班级学习者管理与仿真运行聚合摘要。"""

    def __init__(
        self,
        database: Database,
        practice: PracticeModule,
    ) -> None:
        self._database = database
        self._practice = practice
        self._access = TeachingClassAccess()
        self._mastery_service = MasteryService()

    def get_teacher_dashboard(
        self, class_id: str, teacher: UserView
    ) -> TeacherDashboardView:
        """获取教师专用dashboard数据"""
        with self._database.connect() as connection:
            # 验证教师拥有该班级
            self._access.require_owned_class(connection, class_id, teacher)

            # 获取班级正式成员数量
            member_count_row = connection.execute(
                """
                SELECT COUNT(DISTINCT learner_id) as total_members
                FROM class_memberships
                WHERE class_id = ?
                """,
                (class_id,),
            ).fetchone()

            total_members = member_count_row["total_members"] if member_count_row else 0

            completion_stats = self._calculate_dashboard_completion(
                connection, class_id
            )
            content_completion_rate, at_least_one_completed = (
                completion_stats if completion_stats is not None else (0.0, 0)
            )
            mastery_distribution = self._practice.calculate_mastery_distribution(
                connection, class_id
            )
            consolidation_topics = self._get_consolidation_topics(
                connection, class_id
            )
            homework_summary = self._get_homework_summary(
                connection, class_id
            )
            learner_previews = self._get_learner_previews(
                connection, class_id
            )

            return TeacherDashboardView(
                total_members=total_members,
                content_completion_rate=content_completion_rate,
                at_least_one_completed=at_least_one_completed,
                mastery_distribution=mastery_distribution,
                consolidation_topics=consolidation_topics,
                homework_summary=homework_summary,
                learner_previews=learner_previews,
                insufficient_sample=0 < total_members < 3,
                no_data=total_members == 0,
            )

    def _calculate_dashboard_completion(
        self, connection: sqlite3.Connection, class_id: str
    ) -> tuple[float, int] | None:
        """计算已发布课程内容完成率，作业由独立摘要统计。"""
        content_count = connection.execute(
            """
            SELECT COUNT(*) AS total_contents
            FROM course_contents
            WHERE class_id = ?
              AND publication_status = 'published'
              AND content_type != 'homework'
            """,
            (class_id,),
        ).fetchone()["total_contents"]
        if content_count == 0:
            return None

        completion_rows = connection.execute(
            """
            SELECT cm.learner_id, COUNT(ccc.content_id) AS completed_count
            FROM class_memberships cm
            LEFT JOIN course_content_completions ccc
              ON ccc.class_id = cm.class_id
             AND ccc.learner_id = cm.learner_id
             AND EXISTS (
                 SELECT 1
                 FROM course_contents content
                 WHERE content.id = ccc.content_id
                   AND content.class_id = cm.class_id
                   AND content.publication_status = 'published'
                   AND content.content_type != 'homework'
             )
            WHERE cm.class_id = ?
            GROUP BY cm.learner_id
            """,
            (class_id,),
        ).fetchall()
        if not completion_rows:
            return 0.0, 0

        completed_total = sum(row["completed_count"] for row in completion_rows)
        completed_learners = sum(
            1 for row in completion_rows if row["completed_count"] > 0
        )
        return (
            completed_total / (len(completion_rows) * content_count),
            completed_learners,
        )

    def _get_consolidation_topics(
        self, connection: sqlite3.Connection, class_id: str
    ) -> list[TeacherDashboardConsolidationView]:
        """获取待巩固知识点列表"""
        # 获取所有正式成员
        member_rows = connection.execute(
            """
            SELECT DISTINCT learner_id
            FROM class_memberships
            WHERE class_id = ?
            """,
            (class_id,),
        ).fetchall()

        consolidation_data: dict[str, tuple[int, float]] = {}

        learner_ids = [row["learner_id"] for row in member_rows]
        mastery_summaries = self._mastery_service.get_class_mastery_summaries(
            connection, class_id, learner_ids
        )

        for learner_id in learner_ids:
            for knowledge_point, result in mastery_summaries.get(learner_id, {}).items():
                if result.mastery_level not in {MasteryLevel.UNLEARNED, MasteryLevel.CONSOLIDATING}:
                    continue
                count, score_total = consolidation_data.get(
                    knowledge_point, (0, 0.0)
                )
                consolidation_data[knowledge_point] = (
                    count + 1,
                    score_total + result.weighted_score,
                )

        consolidation_topics = [
            TeacherDashboardConsolidationView(
                knowledge_point=knowledge_point,
                learners_count=count,
                average_mastery=score_total / count,
            )
            for knowledge_point, (count, score_total) in consolidation_data.items()
        ]
        consolidation_topics.sort(
            key=lambda topic: (
                -topic.learners_count,
                topic.average_mastery,
                topic.knowledge_point,
            )
        )
        return consolidation_topics[:5]

    def _get_homework_summary(
        self, connection: sqlite3.Connection, class_id: str
    ) -> TeacherDashboardHomeworkSummaryView:
        """获取作业摘要"""
        # 获取总作业数
        homework_count_row = connection.execute(
            """
            SELECT COUNT(*) as total_homeworks
            FROM course_contents
            WHERE class_id = ? AND content_type = 'homework' AND publication_status = 'published'
            """,
            (class_id,),
        ).fetchone()

        total_homeworks = homework_count_row["total_homeworks"] if homework_count_row else 0

        if total_homeworks == 0:
            return TeacherDashboardHomeworkSummaryView()

        member_count = connection.execute(
            """
            SELECT COUNT(*) AS member_count
            FROM class_memberships
            WHERE class_id = ?
            """,
            (class_id,),
        ).fetchone()["member_count"]
        submission_row = connection.execute(
            """
            SELECT COUNT(*) AS submitted_submissions,
                   SUM(CASE WHEN is_late_submission = 1 THEN 1 ELSE 0 END)
                       AS late_submissions,
                   AVG(total_score) AS average_score
            FROM homework_submissions submission
            WHERE submission.class_id = ?
              AND submission.status = 'submitted'
              AND EXISTS (
                  SELECT 1
                  FROM class_memberships membership
                  WHERE membership.class_id = submission.class_id
                    AND membership.learner_id = submission.learner_id
              )
              AND EXISTS (
                  SELECT 1
                  FROM course_contents homework
                  WHERE homework.id = submission.homework_id
                    AND homework.class_id = submission.class_id
                    AND homework.content_type = 'homework'
                    AND homework.publication_status = 'published'
              )
            """,
            (class_id,),
        ).fetchone()
        expected_submissions = total_homeworks * member_count
        submitted_submissions = submission_row["submitted_submissions"]
        average_score = submission_row["average_score"]

        return TeacherDashboardHomeworkSummaryView(
            total_homeworks=total_homeworks,
            expected_submissions=expected_submissions,
            pending_submissions=expected_submissions - submitted_submissions,
            submitted_submissions=submitted_submissions,
            late_submissions=submission_row["late_submissions"] or 0,
            average_score=round(average_score, 2) if average_score is not None else None,
        )

    def _get_learner_previews(
        self, connection: sqlite3.Connection, class_id: str
    ) -> list[TeacherDashboardLearnerPreviewView]:
        """获取学习者预览（固定上限5个）"""
        # 获取班级正式成员
        member_rows = connection.execute(
            """
            SELECT cm.learner_id, u.display_name
            FROM class_memberships cm
            JOIN users u ON cm.learner_id = u.id
            WHERE cm.class_id = ?
            ORDER BY cm.created_at DESC, cm.rowid DESC
            LIMIT 5
            """,
            (class_id,),
        ).fetchall()

        learner_previews = []

        # 批量获取预览学习者的掌握度（一次查询，避免逐人开连接）
        learner_ids = [row["learner_id"] for row in member_rows]
        mastery_summaries = self._mastery_service.get_class_mastery_summaries(
            connection, class_id, learner_ids
        )

        for member_row in member_rows:
            learner_id = member_row["learner_id"]
            display_name = member_row["display_name"]

            # 获取个人完成率
            completion_rate = self._get_learner_completion_rate(connection, class_id, learner_id)

            # 获取主要掌握度级别
            mastery_level = self._practice.dominant_mastery_level(
                MasteryService.build_level_distribution(mastery_summaries.get(learner_id, {}))
            )

            # 获取最后活动时间
            last_activity = self._get_learner_last_activity(connection, class_id, learner_id)

            learner_previews.append(TeacherDashboardLearnerPreviewView(
                learner_id=learner_id,
                display_name=display_name,
                completion_rate=completion_rate,
                mastery_level=mastery_level,
                last_activity=last_activity
            ))

        return learner_previews

    def _get_learner_completion_rate(
        self, connection: sqlite3.Connection, class_id: str, learner_id: str
    ) -> float:
        """获取学习者个人完成率"""
        # 获取班级已发布内容总数
        content_count_row = connection.execute(
            """
            SELECT COUNT(*) as total_contents
            FROM course_contents
            WHERE class_id = ?
              AND publication_status = 'published'
              AND content_type != 'homework'
            """,
            (class_id,),
        ).fetchone()

        total_contents = content_count_row["total_contents"] if content_count_row else 0

        if total_contents == 0:
            return 0.0

        # 获取学习者完成的内容数
        completion_count_row = connection.execute(
            """
            SELECT COUNT(*) as completed_count
            FROM course_content_completions completion
            WHERE completion.learner_id = ?
              AND completion.class_id = ?
              AND EXISTS (
                  SELECT 1
                  FROM course_contents content
                  WHERE content.id = completion.content_id
                    AND content.class_id = completion.class_id
                    AND content.publication_status = 'published'
                    AND content.content_type != 'homework'
              )
            """,
            (learner_id, class_id),
        ).fetchone()

        completed_count = completion_count_row["completed_count"] if completion_count_row else 0

        return round(completed_count / total_contents, 2)

    def _get_learner_last_activity(
        self, connection: sqlite3.Connection, class_id: str, learner_id: str
    ) -> int | None:
        """获取学习者最后活动时间"""
        # 检查各种活动记录
        activities = []

        # 检查内容完成记录
        completion_row = connection.execute(
            """
            SELECT MAX(completed_at) as last_completion
            FROM course_content_completions
            WHERE learner_id = ? AND class_id = ?
            """,
            (learner_id, class_id),
        ).fetchone()

        if completion_row and completion_row["last_completion"]:
            activities.append(completion_row["last_completion"])

        # 检查作业提交记录
        submission_row = connection.execute(
            """
            SELECT MAX(submitted_at) as last_submission
            FROM homework_submissions
            WHERE learner_id = ? AND class_id = ?
            """,
            (learner_id, class_id),
        ).fetchone()

        if submission_row and submission_row["last_submission"]:
            activities.append(submission_row["last_submission"])

        # 检查练习记录
        practice_row = connection.execute(
            """
            SELECT MAX(activity_at) AS last_practice
            FROM (
                SELECT attempted_at AS activity_at FROM classroom_practice_attempts
                WHERE learner_id = ? AND class_id = ?
                UNION ALL
                SELECT updated_at AS activity_at FROM baseline_practice_runs
                WHERE learner_id = ? AND class_id = ?
            )
            """,
            (learner_id, class_id, learner_id, class_id),
        ).fetchone()

        if practice_row and practice_row["last_practice"]:
            activities.append(practice_row["last_practice"])

        # 返回最新的活动时间
        return max(activities) if activities else None

    def get_class_learners(self, class_id: str, teacher: UserView) -> LearnerListView:
        """获取班级正式成员学习者列表"""
        with self._database.connect() as connection:
            # 验证教师拥有该班级
            self._access.require_owned_class(connection, class_id, teacher)

            # 获取班级正式成员，按加入时间倒序排序
            member_rows = connection.execute(
                """
                SELECT cm.learner_id, u.display_name, cm.created_at
                FROM class_memberships cm
                JOIN users u ON cm.learner_id = u.id
                WHERE cm.class_id = ?
                ORDER BY cm.created_at DESC, cm.rowid DESC
                """,
                (class_id,),
            ).fetchall()

            learner_previews = []
            for member_row in member_rows:
                learner_id = member_row["learner_id"]
                display_name = member_row["display_name"]

                # 计算个人完成率
                completion_rate = self._get_learner_completion_rate(connection, class_id, learner_id)

                # 获取最薄弱知识点
                weakest_knowledge_point = self._get_learner_weakest_knowledge_point(connection, class_id, learner_id)

                learner_previews.append(LearnerPreviewView(
                    learner_id=learner_id,
                    display_name=display_name,
                    completion_rate=completion_rate,
                    weakest_knowledge_point=weakest_knowledge_point,
                    simulation_status="no_data"
                ))

            logger.info(
                "class_learners_listed class_id=%s teacher_id=%s count=%d",
                class_id,
                teacher.id,
                len(learner_previews),
            )

            return LearnerListView(items=learner_previews)

    def get_learner_detail(self, class_id: str, learner_id: str, teacher: UserView) -> LearnerDetailView:
        """获取学习者详情"""
        with self._database.connect() as connection:
            # 验证教师拥有该班级且学习者是班级正式成员
            self._access.require_owned_class(connection, class_id, teacher)

            # 验证学习者是否为班级正式成员
            self._access.require_membership_or_not_found(
                connection, class_id, learner_id,
                code="RESOURCE_NOT_FOUND", message="学习者不存在或不是班级正式成员",
            )

            # 获取学习者基本信息
            learner_row = connection.execute(
                """
                SELECT display_name FROM users
                WHERE id = ?
                """,
                (learner_id,),
            ).fetchone()

            if not learner_row:
                raise BusinessError(
                    status_code=404,
                    code="RESOURCE_NOT_FOUND",
                    message="学习者不存在",
                )

            display_name = learner_row["display_name"]

            # 计算完成统计
            completion_stats = self._calculate_learner_completion_stats(connection, class_id, learner_id)

            # 获取掌握度摘要
            mastery_summary = self._practice.get_mastery_summary(class_id, UserView(id=learner_id, username="", display_name=display_name, role=UserRole.LEARNER, created_at=0))

            logger.info(
                "learner_detail_fetched class_id=%s learner_id=%s teacher_id=%s",
                class_id,
                learner_id,
                teacher.id,
            )

            return LearnerDetailView(
                learner_id=learner_id,
                display_name=display_name,
                completion_stats=completion_stats,
                mastery_summary=mastery_summary,
                simulation_status="no_data",
            )

    @staticmethod
    def _get_simulation_summary(
        connection: sqlite3.Connection, class_id: str, learner_id: str | None = None
    ) -> SimulationSummaryView:
        """从运行表聚合确定性事实；不读取 webots_run_events 的 payload。"""
        params: tuple[str, ...] = (class_id,) if learner_id is None else (class_id, learner_id)
        learner_clause = "" if learner_id is None else " AND learner_id=?"
        connector_params: tuple[str, ...] = (class_id,) if learner_id is None else (class_id, learner_id)
        connector_clause = "" if learner_id is None else " AND learner_id=?"
        connectors = connection.execute(
            f"SELECT COUNT(*) AS count FROM webots_connectors WHERE class_id=?{connector_clause}", connector_params
        ).fetchone()["count"]
        rows = connection.execute(
            f"SELECT status, result_json, updated_at FROM webots_runs WHERE class_id=?{learner_clause} ORDER BY updated_at DESC",
            params,
        ).fetchall()
        latest_terminal = next((row for row in rows if row["status"] in {"completed", "failed"}), None)
        return SimulationSummaryView(
            task_status="no_tasks",
            connector_count=connectors,
            run_count=len(rows),
            running_count=sum(row["status"] in {"created", "running", "dispatched"} for row in rows),
            completed_count=sum(row["status"] == "completed" for row in rows),
            failed_count=sum(row["status"] == "failed" for row in rows),
            latest_terminal_status=latest_terminal["status"] if latest_terminal else None,
            latest_result=json.loads(latest_terminal["result_json"]) if latest_terminal and latest_terminal["result_json"] != "{}" else None,
        )

    def get_teacher_simulation_summary(self, class_id: str, teacher: UserView) -> SimulationSummaryView:
        """教师读取自有班级的仿真聚合，不读取事件正文。"""
        with self._database.connect() as connection:
            self._access.require_owned_class(connection, class_id, teacher)
            return self._get_simulation_summary(connection, class_id)

    def get_teacher_learner_simulation_summary(
        self, class_id: str, learner_id: str, teacher: UserView
    ) -> SimulationSummaryView:
        """教师只读取自有班级正式成员的仿真摘要。"""
        with self._database.connect() as connection:
            self._access.require_owned_class(connection, class_id, teacher)
            self._access.require_membership_or_not_found(
                connection, class_id, learner_id,
                code="RESOURCE_NOT_FOUND", message="学习者不存在或不是班级正式成员",
            )
            return self._get_simulation_summary(connection, class_id, learner_id)

    def _get_learner_weakest_knowledge_point(
        self, connection: sqlite3.Connection, class_id: str, learner_id: str
    ) -> str | None:
        """获取学习者最薄弱知识点"""
        mastery_results = self._mastery_service.get_learner_mastery_summary(
            connection, learner_id, class_id
        )
        if not mastery_results:
            return None
        weakest = min(
            mastery_results.items(),
            key=lambda item: (
                item[1].weighted_score,
                item[0],
            ),
        )
        return weakest[0]

    def _calculate_learner_completion_stats(self, connection: sqlite3.Connection, class_id: str, learner_id: str) -> CourseCompletionStatsView:
        """计算学习者个人完成统计"""
        # 获取班级已发布内容总数
        content_count_row = connection.execute(
            """
            SELECT COUNT(*) as total_contents
            FROM course_contents
            WHERE class_id = ?
              AND publication_status = 'published'
              AND content_type != 'homework'
            """,
            (class_id,),
        ).fetchone()

        total_contents = content_count_row["total_contents"] if content_count_row else 0

        if total_contents == 0:
            return CourseCompletionStatsView(
                total_contents=0,
                completed_contents=0,
                completion_rate=0.0,
            )

        # 获取学习者完成的内容数
        completion_count_row = connection.execute(
            """
            SELECT COUNT(*) as completed_count
            FROM course_content_completions completion
            WHERE completion.learner_id = ?
              AND completion.class_id = ?
              AND EXISTS (
                  SELECT 1
                  FROM course_contents content
                  WHERE content.id = completion.content_id
                    AND content.class_id = completion.class_id
                    AND content.publication_status = 'published'
                    AND content.content_type != 'homework'
              )
            """,
            (learner_id, class_id),
        ).fetchone()

        completed_count = completion_count_row["completed_count"] if completion_count_row else 0

        return CourseCompletionStatsView(
            total_contents=total_contents,
            completed_contents=completed_count,
            completion_rate=round(completed_count / total_contents, 2),
        )
