"""掌握度服务，负责实时计算学习者的知识点掌握度"""

import json
import logging
import sqlite3

from app.teaching_classes.mastery_calculator import MasteryCalculator
from app.teaching_classes.mastery_models import (
    Evidence,
    EvidenceType,
    MasteryCalculationResult,
    MasteryLevel,
    ResultType,
)

logger = logging.getLogger("course_agent.mastery_service")


class KnowledgePointEvidence:
    """知识点证据详情"""

    def __init__(self, knowledge_point: str, evidence: Evidence):
        self.knowledge_point = knowledge_point
        self.evidence = evidence


class MasteryService:
    """掌握度服务。

    所有方法都在调用方持有的连接上查询，不自行开连接：一次请求内的
    掌握度读取共享同一事务边界，批量场景（教师 dashboard）只查一次。
    """

    def _convert_baseline_run_to_evidence(
        self,
        run_row,
    ) -> list[KnowledgePointEvidence]:
        """将基准练习运行转换为证据列表"""
        evidence_list = []

        # 只处理终态记录（completed或abandoned）
        if run_row["status"] not in ["completed", "abandoned"]:
            return evidence_list

        knowledge_points = [
            point.strip()
            for point in json.loads(run_row["knowledge_points"] or "[]")
            if isinstance(point, str) and point.strip()
        ]

        if not knowledge_points:
            return evidence_list

        if run_row["result_type"] is None:
            raise ValueError("终态基准练习缺少 result_type")
        result_type = ResultType(run_row["result_type"])

        # 为每个知识点创建证据
        for knowledge_point in knowledge_points:
            evidence = Evidence.from_result(
                evidence_id=run_row["id"],
                question_id=run_row["content_id"],
                evidence_type=EvidenceType.BASELINE,
                result_type=result_type,
                created_at=run_row["updated_at"],
            )

            evidence_list.append(KnowledgePointEvidence(knowledge_point, evidence))

        return evidence_list

    @staticmethod
    def build_level_distribution(
        mastery_results: dict[str, MasteryCalculationResult],
    ) -> dict[str, int]:
        """统计各掌握度级别下的知识点数量。"""
        level_counts = {
            "unlearned": 0,
            "consolidating": 0,
            "basic_mastery": 0,
            "proficient_mastery": 0,
        }

        for result in mastery_results.values():
            level_counts[result.mastery_level.value] += 1

        return level_counts

    def get_learner_mastery_summary(
        self,
        connection: sqlite3.Connection,
        learner_id: str,
        class_id: str,
    ) -> dict[str, MasteryCalculationResult]:
        """获取学习者在班级内所有知识点的掌握度摘要"""
        return self.get_class_mastery_summaries(connection, class_id, [learner_id])[learner_id]

    def get_class_mastery_summaries(
        self,
        connection: sqlite3.Connection,
        class_id: str,
        learner_ids: list[str] | None = None,
    ) -> dict[str, dict[str, MasteryCalculationResult]]:
        """批量获取班级内多名学习者的掌握度，一次查询后在内存中分组计算。

        learner_ids 为 None 时覆盖班内所有有练习记录的学习者；否则结果覆盖
        每个给定学习者（无练习记录的学习者对应空字典）。
        """
        if learner_ids is not None:
            if not learner_ids:
                return {}
            placeholders = ", ".join("?" for _ in learner_ids)
            run_rows = connection.execute(
                f"""
                SELECT bpr.*
                FROM baseline_practice_runs bpr
                WHERE bpr.class_id = ? AND bpr.learner_id IN ({placeholders})
                ORDER BY bpr.updated_at DESC
                """,
                (class_id, *learner_ids),
            ).fetchall()
        else:
            run_rows = connection.execute(
                """
                SELECT bpr.*
                FROM baseline_practice_runs bpr
                WHERE bpr.class_id = ?
                ORDER BY bpr.updated_at DESC
                """,
                (class_id,),
            ).fetchall()

        # 按学习者、知识点分组证据
        grouped: dict[str, dict[str, list[Evidence]]] = (
            {learner_id: {} for learner_id in learner_ids}
            if learner_ids is not None
            else {}
        )

        for run_row in run_rows:
            learner_evidence = grouped.setdefault(run_row["learner_id"], {})
            for kp_evidence in self._convert_baseline_run_to_evidence(run_row):
                learner_evidence.setdefault(kp_evidence.knowledge_point, []).append(
                    kp_evidence.evidence
                )

        # 逐知识点重放证据计算掌握度
        summaries: dict[str, dict[str, MasteryCalculationResult]] = {}
        for learner_id, evidence_by_kp in grouped.items():
            mastery_results = {}
            for knowledge_point, evidence_list in evidence_by_kp.items():
                result = MasteryCalculator.replay_mastery(evidence_list)
                if result is not None:
                    mastery_results[knowledge_point] = result
            summaries[learner_id] = mastery_results

        return summaries

    def get_next_suggestion(
        self,
        connection: sqlite3.Connection,
        learner_id: str,
        class_id: str,
    ) -> str:
        """获取下一步学习建议；掌握度在同一连接内自取，避免跨连接复算。"""

        mastery_results = self.get_learner_mastery_summary(connection, learner_id, class_id)

        # 1. 检查是否有prompt_shown状态的基准练习需要重试
        prompt_shown_runs = connection.execute(
            """
            SELECT bpr.*, cc.title
            FROM baseline_practice_runs bpr
            JOIN course_contents cc ON bpr.content_id = cc.id
            WHERE bpr.learner_id = ? AND bpr.class_id = ? AND bpr.status = 'prompt_shown'
            ORDER BY bpr.updated_at DESC
            LIMIT 1
            """,
            (learner_id, class_id)
        ).fetchall()

        if prompt_shown_runs:
            run = prompt_shown_runs[0]
            # 解析题目标题
            title = run["title"] or "基准练习"
            return f"重试练习：{title}"

        # 2. 检查最近最终错误且待巩固的知识点
        recent_wrong_runs = connection.execute(
            """
            SELECT bpr.*, cc.title
            FROM baseline_practice_runs bpr
            JOIN course_contents cc ON bpr.content_id = cc.id
            WHERE bpr.learner_id = ? AND bpr.class_id = ?
              AND bpr.status = 'completed' AND bpr.is_correct = 0
            ORDER BY bpr.updated_at DESC
            LIMIT 1
            """,
            (learner_id, class_id)
        ).fetchall()

        if recent_wrong_runs:
            run = recent_wrong_runs[0]
            knowledge_points = json.loads(run["knowledge_points"] or "[]")
            if knowledge_points:
                # 检查该知识点是否处于待巩固状态
                for kp in knowledge_points:
                    if kp in mastery_results:
                        if mastery_results[kp].mastery_level == MasteryLevel.CONSOLIDATING:
                            return f"巩固知识点：{kp}"

        # 3. 跳过仿真失败和可靠提问（无真实数据）

        # 4. 检查当前/首个未完成的课程内容
        next_content = connection.execute(
            """
            SELECT cc.*
            FROM course_contents cc
            LEFT JOIN course_content_completions ccc
              ON cc.id = ccc.content_id AND ccc.learner_id = ? AND ccc.class_id = ?
            WHERE cc.class_id = ? AND cc.publication_status = 'published'
              AND ccc.id IS NULL
            ORDER BY cc.created_at ASC
            LIMIT 1
            """,
            (learner_id, class_id, class_id)
        ).fetchone()

        if next_content:
            return f"继续学习：{next_content['title']}"

        # 5. 全部完成
        return "恭喜！您已完成所有课程内容"

    def get_mastery_summary_for_learner(
        self,
        connection: sqlite3.Connection,
        learner_id: str,
        class_id: str,
    ) -> dict:
        """获取学习者的掌握度摘要（视图字典，键保持既有契约）"""

        mastery_results = self.get_learner_mastery_summary(connection, learner_id, class_id)

        # 构建知识点详情
        knowledge_points_detail = []
        for kp, result in mastery_results.items():
            # 获取最近证据
            recent_evidence = result.used_evidence[0] if result.used_evidence else None

            knowledge_points_detail.append({
                "knowledgePoint": kp,
                "masteryLevel": result.mastery_level.value,
                "weightedScore": result.weighted_score,
                "recentEvidenceCount": result.recent_evidence_count,
                "firstCorrectCount": result.first_correct_count,
                "levelChange": result.level_change,
                "latestEvidence": {
                    "questionId": recent_evidence.question_id if recent_evidence else "",
                    "resultType": recent_evidence.result_type.value if recent_evidence else "",
                    "createdAt": recent_evidence.created_at if recent_evidence else 0
                } if recent_evidence else None
            })

        return {
            "levelDistribution": self.build_level_distribution(mastery_results),
            "knowledgePoints": knowledge_points_detail,
            "totalKnowledgePoints": len(mastery_results)
        }
