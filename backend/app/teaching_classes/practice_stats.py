"""练习统计子模块：掌握度摘要、班级聚合统计。

从 PracticeModule 提取为独立的 PracticeStats 类。
"""
import logging
import sqlite3
from collections.abc import Callable

from app.auth.models import UserView
from app.database import Database
from app.teaching_classes.access import TeachingClassAccess
from app.teaching_classes.mastery_service import MasteryService
from app.teaching_classes.models import (
    ClassAggregateStatsView,
    KnowledgePointMasteryView,
    MasteryDistributionView,
    MasterySummaryView,
)

logger = logging.getLogger("course_agent.practice.stats")


class PracticeStats:
    """练习统计子模块：掌握度摘要、学习建议、班级匿名聚合统计。"""

    def __init__(
        self,
        database: Database,
        now_provider: Callable[[], int],
    ) -> None:
        self._database = database
        self._now = now_provider
        self._access = TeachingClassAccess()
        self._mastery_service = MasteryService()

    def get_mastery_summary(self, class_id: str, learner: UserView) -> MasterySummaryView:
        """获取学习者在班级的掌握度摘要"""
        # 验证学习者是否为班级正式成员
        with self._database.connect() as connection:
            self._access.require_membership(
                connection, class_id, learner.id, message="只有正式成员可以查看掌握度摘要"
            )

        # 获取掌握度摘要
        try:
            with self._database.connect() as connection:
                mastery_data = self._mastery_service.get_mastery_summary_for_learner(
                    connection, learner.id, class_id
                )

            # 构建知识点掌握详情
            knowledge_points = []
            for kp_detail in mastery_data.get("knowledgePoints", []):
                knowledge_points.append(KnowledgePointMasteryView(
                    knowledge_point=kp_detail["knowledgePoint"],
                    mastery_level=kp_detail["masteryLevel"],
                    weighted_score=kp_detail["weightedScore"],
                    recent_evidence_count=kp_detail["recentEvidenceCount"],
                    first_correct_count=kp_detail["firstCorrectCount"],
                    level_change=kp_detail["levelChange"],
                    latest_evidence=kp_detail.get("latestEvidence")
                ))

            return MasterySummaryView(
                status="success",
                message="掌握度分析完成",
                total_knowledge_points=mastery_data.get("totalKnowledgePoints", 0),
                level_distribution=mastery_data.get("levelDistribution", {
                    "unlearned": 0,
                    "consolidating": 0,
                    "basic_mastery": 0,
                    "proficient_mastery": 0
                }),
                knowledge_points=knowledge_points
            )
        except Exception as e:
            logger.error(
                "mastery_summary_error class_id=%s learner_id=%s error=%s",
                class_id, learner.id, str(e)
            )
            # 返回空状态
            return MasterySummaryView(
                status="error",
                message="掌握度分析暂时不可用",
                total_knowledge_points=0,
                level_distribution={
                    "unlearned": 0,
                    "consolidating": 0,
                    "basic_mastery": 0,
                    "proficient_mastery": 0
                },
                knowledge_points=[]
            )

    def get_next_suggestion(self, class_id: str, learner: UserView) -> str:
        """获取下一步学习建议"""
        # 验证学习者是否为班级正式成员
        with self._database.connect() as connection:
            self._access.require_membership(
                connection, class_id, learner.id, message="只有正式成员可以获取学习建议"
            )

        # 获取下一步学习建议（掌握度在建议内部同一连接自取）
        try:
            with self._database.connect() as connection:
                suggestion = self._mastery_service.get_next_suggestion(
                    connection, learner.id, class_id
                )
            return suggestion or "继续学习课程内容"
        except Exception as e:
            logger.error(
                "next_suggestion_error class_id=%s learner_id=%s error=%s",
                class_id, learner.id, str(e)
            )
            return "继续学习课程内容"

    def get_class_aggregate_stats(
        self, class_id: str, learner: UserView
    ) -> ClassAggregateStatsView:
        """获取当前正式学习者所在班级的匿名聚合统计。"""
        with self._database.connect() as connection:
            self._access.require_membership(
                connection, class_id, learner.id, message="只有教学班正式成员可以查看班级学习情况"
            )

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

            # 样本不足检查
            if total_members < 3:
                return ClassAggregateStatsView(
                    status="error",
                    message="样本不足，无法显示聚合统计",
                    insufficient_sample=True,
                )

            # 计算课件平均完成率
            completion_stats = self._calculate_content_completion_rate(
                connection, class_id
            )
            if completion_stats is None:
                return ClassAggregateStatsView(
                    status="error",
                    message="无学习数据",
                    total_members=total_members,
                    no_data=True,
                )

            # 获取掌握度分布
            mastery_distribution = self.calculate_mastery_distribution(connection, class_id)

            return ClassAggregateStatsView(
                status="success",
                message="班级聚合统计获取成功",
                total_members=total_members,
                content_completion_rate=completion_stats[0],
                at_least_one_completed=completion_stats[1],
                mastery_distribution=mastery_distribution,
            )

    def _calculate_content_completion_rate(
        self, connection: sqlite3.Connection, class_id: str
    ) -> tuple[float, int] | None:
        """仅用本班已发布内容与正式成员计算平均完成率。"""
        # 获取班级所有已发布内容数量
        content_count_row = connection.execute(
            """
            SELECT COUNT(*) as total_contents
            FROM course_contents
            WHERE class_id = ? AND publication_status = 'published'
            """,
            (class_id,),
        ).fetchone()

        total_contents = content_count_row["total_contents"] if content_count_row else 0

        if total_contents == 0:
            return None

        # 获取每个成员的完成情况
        member_completion_rows = connection.execute(
            """
            SELECT cm.learner_id, COUNT(ccc.content_id) as completed_count
            FROM class_memberships cm
            LEFT JOIN course_content_completions ccc
              ON cm.learner_id = ccc.learner_id
             AND cm.class_id = ccc.class_id
             AND EXISTS (
                 SELECT 1
                 FROM course_contents published_content
                 WHERE published_content.id = ccc.content_id
                   AND published_content.class_id = cm.class_id
                   AND published_content.publication_status = 'published'
             )
            WHERE cm.class_id = ?
            GROUP BY cm.learner_id
            """,
            (class_id,),
        ).fetchall()

        if not member_completion_rows:
            return None

        # 计算平均完成率和至少完成一项的人数
        total_completion_rate = 0.0
        at_least_one_completed = 0

        for row in member_completion_rows:
            completion_rate = row["completed_count"] / total_contents
            total_completion_rate += completion_rate
            if row["completed_count"] > 0:
                at_least_one_completed += 1

        return total_completion_rate / len(member_completion_rows), at_least_one_completed

    @staticmethod
    def dominant_mastery_level(level_distribution: dict[str, int]) -> str:
        """取知识点数量最多的掌握度层级，无证据时视为未学习。"""
        populated_levels = [
            (level, count)
            for level, count in level_distribution.items()
            if count > 0
        ]
        return (
            max(populated_levels, key=lambda item: item[1])[0]
            if populated_levels
            else "unlearned"
        )

    def calculate_mastery_distribution(
        self, connection: sqlite3.Connection, class_id: str
    ) -> MasteryDistributionView:
        """把每名正式成员归入其知识点中占比最高的掌握度层级。"""
        mastery_rows = connection.execute(
            """
            SELECT DISTINCT learner_id
            FROM class_memberships
            WHERE class_id = ?
            """,
            (class_id,),
        ).fetchall()
        distribution = {
            "unlearned": 0,
            "consolidating": 0,
            "basic_mastery": 0,
            "proficient_mastery": 0,
        }

        learner_ids = [row["learner_id"] for row in mastery_rows]
        mastery_summaries = self._mastery_service.get_class_mastery_summaries(
            connection, class_id, learner_ids
        )

        for learner_id in learner_ids:
            level_distribution = MasteryService.build_level_distribution(
                mastery_summaries.get(learner_id, {})
            )
            distribution[self.dominant_mastery_level(level_distribution)] += 1

        return MasteryDistributionView(**distribution)
