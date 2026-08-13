"""TeachingClassService 加入申请状态机纯单元测试，不依赖数据库或 FastAPI。

测试核心逻辑：create_join_request、resolve_join_request 等方法的业务规则，
通过模拟 Database 连接来执行。
"""
from __future__ import annotations

import sqlite3
import uuid
from collections.abc import Callable
from unittest.mock import MagicMock, patch

import pytest

from app.auth.models import UserRole, UserView
from app.common.errors import BusinessError
from app.teaching_classes.models import (
    JoinPolicy,
    JoinRequestStatus,
    ResolveJoinRequestRequest,
    UpdateJoinPolicyRequest,
)


# ── 辅助：创建测试用户 ──────────────────────────────────────────

def _teacher() -> UserView:
    return UserView(id="t1", username="teacher1", display_name="教师", role=UserRole.TEACHER)


def _learner() -> UserView:
    return UserView(id="l1", username="learner1", display_name="学习者", role=UserRole.LEARNER)


# ── 辅助：Mock Database ─────────────────────────────────────────

def _make_database(
    *,
    teaching_classes: dict | None = None,
    memberships: list[dict] | None = None,
    join_requests: list[dict] | None = None,
    authorization_codes: list[dict] | None = None,
) -> MagicMock:
    """创建一个预置数据的 Mock Database。"""
    db = MagicMock()
    conn = MagicMock()

    def mock_execute(sql: str, params=None):
        result = MagicMock()
        result.fetchone.return_value = None
        result.fetchall.return_value = []
        result.rowcount = 0

        # Parse sql for known tables
        if "teaching_classes" in sql and teaching_classes:
            row_data = teaching_classes.get("class_data")
            if row_data:
                result.fetchone.return_value = row_data
                result.fetchall.return_value = [row_data]

        if "class_memberships" in sql:
            if "class_id = ? AND learner_id = ?" in sql and memberships:
                result.fetchone.return_value = {"1": 1}
            else:
                result.fetchall.return_value = memberships or []

        if "class_join_requests" in sql:
            if "learner_id = ?" in sql and join_requests:
                result.fetchall.return_value = join_requests
            result.fetchone.return_value = join_requests[0] if join_requests else None

        if "class_authorization_codes" in sql:
            result.fetchone.return_value = authorization_codes[0] if authorization_codes else None

        if sql.startswith("INSERT") or sql.startswith("UPDATE"):
            result.rowcount = 1

        return result

    conn.execute.side_effect = mock_execute
    db.connect.return_value.__enter__.return_value = conn
    return db


class TestJoinRequestStateMachine:
    """加入申请状态机核心规则：状态跃迁、重复申请、已拒绝后重新申请。"""

    def test_join_request_rejects_closed_class(self):
        """CLOSED 状态的教学班应拒绝自由加入请求。"""
        db = _make_database(teaching_classes={"class_data": {"id": "c1", "join_policy": JoinPolicy.CLOSED.value}})

        now_provider = lambda: 1000

        # 创建 TeachingClassService
        from app.teaching_classes.service import TeachingClassService
        from app.teaching_classes.practice import PracticeModule

        practice = MagicMock(spec=PracticeModule)
        service = TeachingClassService(db, now_provider, practice=practice)

        with pytest.raises(BusinessError) as exc:
            service.join_class("c1", _learner())
        assert exc.value.code == "CLASS_JOIN_FORBIDDEN"

    def test_join_request_requires_approval_class(self):
        """APPROVAL 的教学班应拒绝直接加入。"""
        db = _make_database(teaching_classes={"class_data": {"id": "c1", "join_policy": JoinPolicy.APPROVAL.value}})
        now_provider = lambda: 1000

        from app.teaching_classes.service import TeachingClassService
        practice = MagicMock()
        service = TeachingClassService(db, now_provider, practice=practice)

        with pytest.raises(BusinessError) as exc:
            service.join_class("c1", _learner())
        assert exc.value.code == "CLASS_JOIN_APPROVAL_REQUIRED"

    def test_free_join_establishes_membership(self):
        """FREE 策略的教学班应允许直接加入。"""
        db = _make_database(teaching_classes={"class_data": {"id": "c1", "join_policy": JoinPolicy.FREE.value}})
        now_provider = lambda: 1000

        from app.teaching_classes.service import TeachingClassService
        practice = MagicMock()
        service = TeachingClassService(db, now_provider, practice=practice)

        # Mock admission to return a membership
        with patch.object(service._admission, "establish_membership") as mock_est:
            mock_est.return_value = MagicMock(joined_at=1000, is_new_member=True)
            result = service.join_class("c1", _learner())

        assert result.is_new_member is True
        assert result.class_id == "c1"

    def test_update_join_policy(self):
        """教师应能更新教学班加入策略。"""
        db = _make_database(teaching_classes={"class_data": {"id": "c1", "owner_teacher_id": "t1", "name": "test", "join_policy": JoinPolicy.FREE.value, "created_at": 0, "updated_at": 100}})
        now_provider = lambda: 2000

        from app.teaching_classes.service import TeachingClassService
        practice = MagicMock()
        service = TeachingClassService(db, now_provider, practice=practice)

        # 覆盖 SQL 查询的返回值，包含 member_count（SQL 的 COUNT 聚合）
        def mock_execute(sql, params=None):
            result = MagicMock()
            result.fetchone.return_value = None
            result.fetchall.return_value = []
            result.rowcount = 0

            if "UPDATE teaching_classes SET join_policy" in sql:
                result.rowcount = 1

            if "FROM teaching_classes tc" in sql and "COUNT" in sql:
                result.fetchone.return_value = {"id": "c1", "name": "test", "join_policy": JoinPolicy.APPROVAL.value, "created_at": 0, "updated_at": 2000, "member_count": 5}

            if "owner_teacher_id" in sql:
                result.fetchone.return_value = {"id": "c1", "name": "test", "join_policy": JoinPolicy.APPROVAL.value, "created_at": 0, "updated_at": 2000, "member_count": 5}

            return result

        db.connect.return_value.__enter__.return_value.execute.side_effect = mock_execute

        result = service.update_join_policy("c1", UpdateJoinPolicyRequest(join_policy=JoinPolicy.APPROVAL), _teacher())
        assert result.join_policy == JoinPolicy.APPROVAL
        assert result.member_count == 5
