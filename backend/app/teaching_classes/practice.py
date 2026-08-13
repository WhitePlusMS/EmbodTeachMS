"""练习模块 Facade：组合课堂练习、统计子模块，保留基准练习状态机持久化逻辑。

通过子模块拆分解决单一文件过长问题，保持所有 public 方法签名不变。
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
from app.teaching_classes.baseline_practice import BaselinePracticeStateMachine
from app.teaching_classes.baseline_practice_models import (
    BaselinePracticeDetail,
    BaselinePracticeResult,
    BaselinePracticeStatus,
)
from app.teaching_classes.classroom_practice import ClassroomPractice
from app.teaching_classes.models import (
    ClassAggregateStatsView,
    ClassroomPracticeAnswerRequest,
    ClassroomPracticeContentDetailView,
    ClassroomPracticeResultView,
    ContentType,
    MasteryDistributionView,
    MasterySummaryView,
    PublishedQuestionView,
)
from app.teaching_classes.practice_stats import PracticeStats

logger = logging.getLogger("course_agent.practice")

# baseline_practice_runs 的主键与创建时间列：命名映射写入时不在 UPDATE 中回写
_BASELINE_RUN_READONLY_COLUMNS = frozenset({"learner_id", "class_id", "content_id", "created_at"})


def to_published_question(row: sqlite3.Row) -> PublishedQuestionView | None:
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


def check_answer_correct(selected_answers: list[int], correct_answers: list[int]) -> bool:
    """核对答案是否正确"""
    # 未选择答案时返回错误
    if not selected_answers:
        return False

    # 检查答案集合是否完全匹配
    return set(selected_answers) == set(correct_answers)


class PracticeModule:
    """学习者练习与掌握度模块：组合子模块提供统一接口。

    内部组合：
    - ClassroomPractice：课堂练习作答
    - PracticeStats：掌握度摘要与班级聚合统计
    - 基准练习相关逻辑（状态机持久化包装）保留在此
    """

    def __init__(
        self,
        database: Database,
        now_provider: Callable[[], int],
    ) -> None:
        self._database = database
        self._now = now_provider
        self._access = TeachingClassAccess()

        # 子模块
        self._classroom = ClassroomPractice(database, now_provider)
        self._stats = PracticeStats(database, now_provider)

    # ── 课堂练习：委托给 ClassroomPractice ─────────────────────────

    def get_classroom_practice_content_detail(
        self, class_id: str, content_id: str, learner: UserView
    ) -> ClassroomPracticeContentDetailView:
        return self._classroom.get_classroom_practice_content_detail(class_id, content_id, learner)

    def submit_classroom_practice_answer(
        self, request: ClassroomPracticeAnswerRequest, learner: UserView
    ) -> ClassroomPracticeResultView:
        return self._classroom.submit_classroom_practice_answer(request, learner)

    # ── 基准练习：状态机持久化包装 ────────────────────────────────

    def get_baseline_practice_detail(
        self, class_id: str, content_id: str, learner: UserView
    ) -> BaselinePracticeDetail:
        """获取基准练习状态；首次访问时建立唯一的 INITIAL 运行。"""
        with self._database.connect() as connection:
            content_row = self._get_baseline_content(connection, class_id, content_id, learner)
            machine = self._load_or_create_baseline_machine(
                connection, content_row, learner.id, class_id, content_id
            )
            return machine.get_detail()

    def submit_baseline_practice_answer(
        self,
        class_id: str,
        content_id: str,
        selected_answers: list[int],
        learner: UserView,
    ) -> BaselinePracticeResult:
        """提交基准练习答案并持久化状态转移。"""
        with self._database.connect() as connection:
            content_row = self._get_baseline_content(connection, class_id, content_id, learner)
            machine = self._load_or_create_baseline_machine(
                connection, content_row, learner.id, class_id, content_id
            )

            result = machine.submit_answer(selected_answers)
            self._update_baseline_run(connection, machine)
            logger.info(
                "baseline_practice_answer_submitted learner_id=%s class_id=%s content_id=%s status=%s",
                learner.id,
                class_id,
                content_id,
                machine.status.value,
            )
            return result

    def abandon_baseline_practice(
        self,
        class_id: str,
        content_id: str,
        learner: UserView,
    ) -> BaselinePracticeResult:
        """放弃基准练习"""
        with self._database.connect() as connection:
            content_row = self._get_baseline_content(connection, class_id, content_id, learner)
            machine = self._load_or_create_baseline_machine(
                connection, content_row, learner.id, class_id, content_id
            )

            result = machine.abandon()
            self._update_baseline_run(connection, machine)
            logger.info(
                "baseline_practice_abandoned learner_id=%s class_id=%s content_id=%s status=%s",
                learner.id,
                class_id,
                content_id,
                machine.status.value,
            )
            return result

    # ── 掌握度统计：委托给 PracticeStats ───────────────────────────

    def get_mastery_summary(self, class_id: str, learner: UserView) -> MasterySummaryView:
        return self._stats.get_mastery_summary(class_id, learner)

    def get_next_suggestion(self, class_id: str, learner: UserView) -> str:
        return self._stats.get_next_suggestion(class_id, learner)

    def get_class_aggregate_stats(
        self, class_id: str, learner: UserView
    ) -> ClassAggregateStatsView:
        return self._stats.get_class_aggregate_stats(class_id, learner)

    def calculate_mastery_distribution(
        self, connection: sqlite3.Connection, class_id: str
    ) -> MasteryDistributionView:
        """把每名正式成员归入其知识点中占比最高的掌握度层级。"""
        return self._stats.calculate_mastery_distribution(connection, class_id)

    @staticmethod
    def dominant_mastery_level(level_distribution: dict[str, int]) -> str:
        """取知识点数量最多的掌握度层级，无证据时视为未学习。"""
        return PracticeStats.dominant_mastery_level(level_distribution)

    # ── 基准练习内部辅助方法 ──────────────────────────────────────

    def _get_baseline_content(
        self, connection: sqlite3.Connection, class_id: str, content_id: str, learner: UserView
    ) -> sqlite3.Row:
        """验证成员和题目，并返回基准练习所需的来源元数据。"""
        self._access.require_membership(
            connection, class_id, learner.id, message="只有正式成员可以访问基准练习"
        )
        row = connection.execute(
            """
            SELECT
                cc.*, cq.question_type, cq.correct_answers_json,
                cq.knowledge_points_json, cq.explanation,
                ps.original_filename AS source_filename
            FROM course_contents cc
            JOIN course_content_questions cq ON cq.content_id = cc.id
            LEFT JOIN preparation_sessions ps ON ps.class_id = cc.class_id
            WHERE cc.id = ? AND cc.class_id = ? AND cc.publication_status = 'published'
            LIMIT 1
            """,
            (content_id, class_id),
        ).fetchone()
        if row is None:
            raise BusinessError(
                status_code=404,
                code="RESOURCE_NOT_FOUND",
                message="基准练习不存在或未发布",
            )
        if row["content_type"] != ContentType.QUESTION.value:
            raise BusinessError(
                status_code=400,
                code="INVALID_CONTENT_TYPE",
                message="该内容不是基准练习题目",
            )
        return row

    def _new_baseline_machine(
        self, content_row: sqlite3.Row, learner_id: str, class_id: str, content_id: str
    ) -> BaselinePracticeStateMachine:
        return BaselinePracticeStateMachine(
            learner_id=learner_id,
            class_id=class_id,
            content_id=content_id,
            correct_answers=json.loads(content_row["correct_answers_json"]),
            explanation=content_row["explanation"],
            question_type=content_row["question_type"],
            knowledge_points=json.loads(content_row["knowledge_points_json"]),
            source=content_row["source_filename"] or "课程已发布内容",
            score=1,
        )

    def _baseline_machine_from_row(self, row: sqlite3.Row) -> BaselinePracticeStateMachine:
        machine = BaselinePracticeStateMachine(
            learner_id=row["learner_id"],
            class_id=row["class_id"],
            content_id=row["content_id"],
            correct_answers=json.loads(row["correct_answers"]),
            explanation=row["explanation"],
            question_type=row["question_type"],
            difficulty=row["difficulty"],
            knowledge_points=json.loads(row["knowledge_points"]),
            source=row["source"],
            score=row["score"],
        )
        machine.status = BaselinePracticeStatus(row["status"])
        machine.first_attempt_answers = json.loads(row["first_attempt_answers"])
        machine.second_attempt_answers = json.loads(row["second_attempt_answers"])
        machine.final_answers = json.loads(row["final_answers"])
        machine.created_at = row["created_at"]
        machine.updated_at = row["updated_at"]
        return machine

    def _load_or_create_baseline_machine(
        self,
        connection: sqlite3.Connection,
        content_row: sqlite3.Row,
        learner_id: str,
        class_id: str,
        content_id: str,
    ) -> BaselinePracticeStateMachine:
        """读取唯一的基准练习运行；不存在时创建 INITIAL 运行（三个入口共用）。

        唯一约束 UNIQUE(learner_id, class_id, content_id) 兜底并发创建：
        写入被忽略时回读已存在的运行。
        """
        run_row = self._select_baseline_run(connection, learner_id, class_id, content_id)
        if run_row is None:
            machine = self._new_baseline_machine(content_row, learner_id, class_id, content_id)
            if self._insert_baseline_run(connection, machine):
                return machine
            # 并发下被其他请求抢先创建，回读已存在的运行
            run_row = self._select_baseline_run(connection, learner_id, class_id, content_id)
        return self._baseline_machine_from_row(run_row)

    @staticmethod
    def _select_baseline_run(
        connection: sqlite3.Connection, learner_id: str, class_id: str, content_id: str
    ) -> sqlite3.Row | None:
        return connection.execute(
            """
            SELECT * FROM baseline_practice_runs
            WHERE learner_id = ? AND class_id = ? AND content_id = ?
            """,
            (learner_id, class_id, content_id),
        ).fetchone()

    def _insert_baseline_run(
        self, connection: sqlite3.Connection, machine: BaselinePracticeStateMachine
    ) -> bool:
        """写入新运行；唯一约束冲突时忽略写入并返回 False。"""
        row = {"id": str(uuid.uuid4()), **self._baseline_run_row(machine)}
        columns = ", ".join(row)
        placeholders = ", ".join(f":{name}" for name in row)
        cursor = connection.execute(
            f"INSERT OR IGNORE INTO baseline_practice_runs ({columns}) VALUES ({placeholders})",
            row,
        )
        return cursor.rowcount == 1

    def _update_baseline_run(
        self, connection: sqlite3.Connection, machine: BaselinePracticeStateMachine
    ) -> None:
        row = self._baseline_run_row(machine)
        assignments = ", ".join(
            f"{name} = :{name}"
            for name in row
            if name not in _BASELINE_RUN_READONLY_COLUMNS
        )
        connection.execute(
            f"""
            UPDATE baseline_practice_runs SET
                {assignments}
            WHERE learner_id = :learner_id AND class_id = :class_id AND content_id = :content_id
            """,
            row,
        )

    def _baseline_run_row(
        self, machine: BaselinePracticeStateMachine
    ) -> dict[str, object]:
        """状态机到 baseline_practice_runs 列的命名映射，INSERT/UPDATE 共用。"""
        detail = machine.get_detail()
        return {
            "learner_id": machine.learner_id,
            "class_id": machine.class_id,
            "content_id": machine.content_id,
            "status": machine.status.value,
            "first_attempt_answers": json.dumps(machine.first_attempt_answers, separators=(",", ":")),
            "second_attempt_answers": json.dumps(machine.second_attempt_answers, separators=(",", ":")),
            "final_answers": json.dumps(machine.final_answers, separators=(",", ":")),
            "is_correct": detail.is_correct,
            "correct_answers": json.dumps(machine.correct_answers, separators=(",", ":")),
            "explanation": machine.explanation,
            "question_type": machine.question_type,
            "difficulty": machine.difficulty,
            "knowledge_points": json.dumps(machine.knowledge_points, separators=(",", ":")),
            "source": machine.source,
            "score": machine.score,
            "result_type": detail.result_type.value if detail.result_type else None,
            "created_at": machine.created_at,
            "updated_at": machine.updated_at,
        }
