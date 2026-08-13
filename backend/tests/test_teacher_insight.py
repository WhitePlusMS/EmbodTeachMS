"""TeacherInsightModule 纯单元测试。

测试教师仪表盘的关键计算逻辑：
- _calculate_dashboard_completion: 完成率计算
- _get_homework_summary: 作业摘要统计
- _get_learner_completion_rate: 个人完成率
- _get_learner_last_activity: 最后活动时间
- _calculate_learner_completion_stats: 个人完成统计

使用 :memory: SQLite 和 mock 的 PracticeModule/MasteryService。
"""
from __future__ import annotations

import sqlite3
import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.auth.models import UserRole, UserView
from app.database import Database
from app.teaching_classes.teacher_insight import TeacherInsightModule


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test_teacher_insight.db"


@pytest.fixture
def database(db_path) -> Database:
    db = Database(db_path)
    db.initialize()
    return db


@pytest.fixture
def practice_mock():
    """模拟 PracticeModule。"""
    mock = MagicMock()
    mock.calculate_mastery_distribution.return_value = {"learned": 0, "practicing": 0, "consolidating": 0, "unlearned": 0}
    mock.dominant_mastery_level.return_value = "unlearned"
    mock.get_mastery_summary.return_value = {"learned": 0, "practicing": 0, "consolidating": 0, "unlearned": 0}
    return mock


@pytest.fixture
def teacher() -> UserView:
    return UserView(id="teacher-1", username="teacher1", display_name="教师1", role=UserRole.TEACHER, created_at=0)


@pytest.fixture
def insight(database, practice_mock) -> TeacherInsightModule:
    return TeacherInsightModule(database, practice_mock)


def _seed_class_and_teacher(database: Database, class_id: str, teacher_id: str, now: int = 1000) -> None:
    """创建测试教学班和教师关联。"""
    with database.connect() as connection:
        connection.execute(
            "INSERT INTO users(id, username, password_hash, display_name, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (teacher_id, "teacher1", "hash", "教师1", "teacher", now),
        )
        connection.execute(
            "INSERT INTO teaching_classes(id, owner_teacher_id, name, join_policy, background, introduction, objectives, features, created_at, updated_at) VALUES (?, ?, ?, ?, '', '', '', '', ?, ?)",
            (class_id, teacher_id, "测试班", "free", now, now),
        )
        connection.commit()


def _seed_learners(database: Database, class_id: str, count: int = 3, now: int = 1000) -> list[str]:
    """创建 learners 并加入班级。"""
    learner_ids = []
    with database.connect() as connection:
        for i in range(count):
            lid = f"learner-{i}"
            learner_ids.append(lid)
            connection.execute(
                "INSERT OR IGNORE INTO users(id, username, password_hash, display_name, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (lid, f"learner{i}", "hash", f"学习者{i}", "learner", now),
            )
            connection.execute(
                "INSERT INTO class_memberships(class_id, learner_id, created_at) VALUES (?, ?, ?)",
                (class_id, lid, now),
            )
        connection.commit()
    return learner_ids


def _seed_course_content(database: Database, class_id: str, content_count: int = 3, now: int = 1000) -> list[str]:
    """创建已发布课程内容。"""
    content_ids = []
    with database.connect() as connection:
        for i in range(content_count):
            cid = f"content-{i}"
            content_ids.append(cid)
            connection.execute(
                "INSERT INTO course_contents(id, class_id, title, content_type, publication_status, created_at, updated_at) VALUES (?, ?, ?, ?, 'published', ?, ?)",
                (cid, class_id, f"课程{i}", "knowledge_point", now, now),
            )
        connection.commit()
    return content_ids


def _seed_completions(database: Database, class_id: str, learner_ids: list[str], content_ids: list[str], now: int = 1000) -> None:
    """创建完成记录。"""
    with database.connect() as connection:
        for lid in learner_ids:
            for i, cid in enumerate(content_ids):
                if i == 0:  # 每个学习者完成了第一个内容
                    connection.execute(
                        "INSERT INTO course_content_completions(learner_id, class_id, content_id, completed_at, created_at) VALUES (?, ?, ?, ?, ?)",
                        (lid, class_id, cid, now, now),
                    )
        connection.commit()


# ── _calculate_dashboard_completion ─────────────────────────────


class TestDashboardCompletion:
    def test_no_content_returns_none(self, insight, database):
        class_id = "class-no-content"
        _seed_class_and_teacher(database, class_id, "t1")
        with database.connect() as connection:
            result = insight._calculate_dashboard_completion(connection, class_id)
        assert result is None

    def test_all_learners_completed_first_content(self, insight, database):
        class_id = "class-completed"
        _seed_class_and_teacher(database, class_id, "t1")
        learners = _seed_learners(database, class_id, 2)
        contents = _seed_course_content(database, class_id, 3)
        _seed_completions(database, class_id, learners, contents)

        with database.connect() as connection:
            rate, learners_with_at_least_one = insight._calculate_dashboard_completion(connection, class_id)

        # 2 个学习者 x 3 个内容 = 6 总完成量，实际完成 2（每人完成1个）
        assert rate == pytest.approx(2 / 6, rel=0.01)
        assert learners_with_at_least_one == 2

    def test_no_learners_returns_defaults(self, insight, database):
        class_id = "class-no-learners"
        _seed_class_and_teacher(database, class_id, "t1")
        _seed_course_content(database, class_id, 2)

        with database.connect() as connection:
            rate, count = insight._calculate_dashboard_completion(connection, class_id)

        assert rate == pytest.approx(0.0, rel=0.01)
        assert count == 0


# ── _get_learner_completion_rate ────────────────────────────────────


class TestLearnerCompletionRate:
    def test_returns_zero_when_no_content(self, insight, database):
        class_id = "class-rate"
        _seed_class_and_teacher(database, class_id, "t1")
        _seed_learners(database, class_id, 1)

        with database.connect() as connection:
            rate = insight._get_learner_completion_rate(connection, class_id, "learner-0")
        assert rate == 0.0

    def test_learner_completed_half_of_content(self, insight, database):
        class_id = "class-rate-half"
        _seed_class_and_teacher(database, class_id, "t1")
        _seed_learners(database, class_id, 1)
        contents = _seed_course_content(database, class_id, 4)

        with database.connect() as connection:
            # 手动完成前2个
            import time
            now = int(time.time())
            for cid in contents[:2]:
                connection.execute(
                    "INSERT INTO course_content_completions(learner_id, class_id, content_id, completed_at, created_at) VALUES (?, ?, ?, ?, ?)",
                    ("learner-0", class_id, cid, now, now),
                )
            connection.commit()
            rate = insight._get_learner_completion_rate(connection, class_id, "learner-0")
        assert rate == pytest.approx(0.5, rel=0.01)

    def test_learner_completed_all_content(self, insight, database):
        class_id = "class-rate-all"
        _seed_class_and_teacher(database, class_id, "t1")
        _seed_learners(database, class_id, 1)
        contents = _seed_course_content(database, class_id, 3)

        with database.connect() as connection:
            import time
            now = int(time.time())
            for cid in contents:
                connection.execute(
                    "INSERT INTO course_content_completions(learner_id, class_id, content_id, completed_at, created_at) VALUES (?, ?, ?, ?, ?)",
                    ("learner-0", class_id, cid, now, now),
                )
            connection.commit()
            rate = insight._get_learner_completion_rate(connection, class_id, "learner-0")
        assert rate == pytest.approx(1.0, rel=0.01)


# ── _get_homework_summary ───────────────────────────────────────


class TestHomeworkSummary:
    def test_no_homework_returns_default(self, insight, database):
        class_id = "class-no-hw"
        _seed_class_and_teacher(database, class_id, "t1")
        with database.connect() as connection:
            summary = insight._get_homework_summary(connection, class_id)
        assert summary.total_homeworks == 0
        assert summary.expected_submissions == 0

    def test_homework_available_returns_stats(self, insight, database):
        class_id = "class-hw"
        _seed_class_and_teacher(database, class_id, "t1")
        learners = _seed_learners(database, class_id, 2)
        with database.connect() as connection:
            # 创建作业内容
            connection.execute(
                "INSERT INTO course_contents(id, class_id, title, content_type, publication_status, created_at, updated_at) VALUES (?, ?, ?, 'homework', 'published', ?, ?)",
                ("hw-1", class_id, "作业1", 1000, 1000),
            )
            connection.commit()
            summary = insight._get_homework_summary(connection, class_id)
        assert summary.total_homeworks == 1
        assert summary.expected_submissions == 1 * 2  # 1 作业 x 2 学习者


# ── _get_learner_last_activity ─────────────────────────────────────


class TestLearnerLastActivity:
    def test_no_activity_returns_none(self, insight, database):
        class_id = "class-activity"
        _seed_class_and_teacher(database, class_id, "t1")
        with database.connect() as connection:
            result = insight._get_learner_last_activity(connection, class_id, "learner-none")
        assert result is None

    def test_returns_latest_completion_time(self, insight, database):
        class_id = "class-activity-comp"
        _seed_class_and_teacher(database, class_id, "t1")
        learners = _seed_learners(database, class_id, 1)
        contents = _seed_course_content(database, class_id, 2)
        _seed_completions(database, class_id, learners, contents)

        with database.connect() as connection:
            result = insight._get_learner_last_activity(connection, class_id, "learner-0")
        assert result is not None
        assert result == 1000  # 和 seeded completion 时间一致


# ── _calculate_learner_completion_stats ────────────────────────────


class TestLearnerCompletionStats:
    def test_no_content_stats(self, insight, database):
        class_id = "class-stats"
        _seed_class_and_teacher(database, class_id, "t1")
        with database.connect() as connection:
            stats = insight._calculate_learner_completion_stats(connection, class_id, "learner-none")
        assert stats.total_contents == 0
        assert stats.completed_contents == 0
        assert stats.completion_rate == 0.0

    def test_learner_stats_matches_expected(self, insight, database):
        class_id = "class-stats-ok"
        _seed_class_and_teacher(database, class_id, "t1")
        _seed_learners(database, class_id, 1)
        contents = _seed_course_content(database, class_id, 4)

        with database.connect() as connection:
            import time
            now = int(time.time())
            for cid in contents:
                connection.execute(
                    "INSERT INTO course_content_completions(learner_id, class_id, content_id, completed_at, created_at) VALUES (?, ?, ?, ?, ?)",
                    ("learner-0", class_id, cid, now, now),
                )
            connection.commit()
            stats = insight._calculate_learner_completion_stats(connection, class_id, "learner-0")
        assert stats.total_contents == 4
        assert stats.completed_contents == 4
        assert stats.completion_rate == 1.0


# ── get_teacher_dashboard 集成 ────────────────────────────────────


class TestTeacherDashboard:
    def test_dashboard_returns_for_teacher(self, insight, database, teacher):
        class_id = "class-dash"
        _seed_class_and_teacher(database, class_id, teacher.id)
        learners = _seed_learners(database, class_id, 2)
        _seed_course_content(database, class_id, 3)
        _seed_completions(database, class_id, learners, ["content-0", "content-1"])

        dashboard = insight.get_teacher_dashboard(class_id, teacher)
        assert dashboard.total_members == 2
        assert dashboard.insufficient_sample is True  # 2 < 3
        assert dashboard.no_data is False

    def test_dashboard_empty_class(self, insight, database, teacher):
        class_id = "class-empty"
        _seed_class_and_teacher(database, class_id, teacher.id)

        dashboard = insight.get_teacher_dashboard(class_id, teacher)
        assert dashboard.total_members == 0
        assert dashboard.no_data is True

    def test_dashboard_returns_homework_summary(self, insight, database, teacher):
        class_id = "class-hw-dash"
        _seed_class_and_teacher(database, class_id, teacher.id)
        _seed_learners(database, class_id, 2)

        with database.connect() as connection:
            connection.execute(
                "INSERT INTO course_contents(id, class_id, title, content_type, publication_status, created_at, updated_at) VALUES (?, ?, ?, 'homework', 'published', ?, ?)",
                ("hw-dash-1", class_id, "作业1", 1000, 1000),
            )
            connection.commit()

        dashboard = insight.get_teacher_dashboard(class_id, teacher)
        assert dashboard.homework_summary.total_homeworks == 1


# ── get_class_learners ──────────────────────────────────────────


class TestGetClassLearners:
    def test_returns_learner_list_for_teacher(self, insight, database, teacher):
        class_id = "class-learners"
        _seed_class_and_teacher(database, class_id, teacher.id)
        _seed_learners(database, class_id, 3)

        result = insight.get_class_learners(class_id, teacher)
        assert len(result.items) == 3

    def test_learner_preview_has_completion_rate(self, insight, database, teacher):
        class_id = "class-learners-rate"
        _seed_class_and_teacher(database, class_id, teacher.id)
        _seed_learners(database, class_id, 1)
        _seed_course_content(database, class_id, 2)

        result = insight.get_class_learners(class_id, teacher)
        assert len(result.items) == 1
        assert result.items[0].completion_rate == 0.0  # 未完成任何内容
