"""
TeachingClassAccess 与 TeachingClassAdmission 纯单元测试。

使用 :memory: SQLite 真实数据库，零 HTTP，零 Mock 框架。
"""

import sqlite3
from dataclasses import dataclass

import pytest

from app.auth.models import UserView
from app.common.errors import BusinessError
from app.teaching_classes.access import TeachingClassAccess
from app.teaching_classes.admission import MembershipAdmission, TeachingClassAdmission
from app.teaching_classes.models import JoinRequestStatus, ResolveJoinRequestRequest


# ── helpers ──────────────────────────────────────────────────────────

@dataclass
class _Schemas:
    """测试用建表语句集合。"""

    TEACHING_CLASSES: str = """
        CREATE TABLE teaching_classes (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            owner_teacher_id TEXT NOT NULL,
            join_policy TEXT NOT NULL DEFAULT 'approval',
            member_count INTEGER NOT NULL DEFAULT 0,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        )
    """
    CLASS_MEMBERSHIPS: str = """
        CREATE TABLE class_memberships (
            class_id TEXT NOT NULL,
            learner_id TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            PRIMARY KEY (class_id, learner_id)
        )
    """
    CLASS_JOIN_REQUESTS: str = """
        CREATE TABLE class_join_requests (
            id TEXT PRIMARY KEY,
            class_id TEXT NOT NULL,
            learner_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at INTEGER NOT NULL,
            resolved_at INTEGER,
            resolved_by_teacher_id TEXT
        )
    """


@pytest.fixture
def teacher() -> UserView:
    return UserView(
        id="teacher-01",
        username="t1",
        display_name="教师一号",
        role="teacher",
    )


@pytest.fixture
def learner() -> UserView:
    return UserView(
        id="learner-01",
        username="l1",
        display_name="学习者一号",
        role="learner",
    )


@pytest.fixture
def access() -> TeachingClassAccess:
    return TeachingClassAccess()


@pytest.fixture
def conn() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    schemas = _Schemas()
    connection.execute(schemas.TEACHING_CLASSES)
    connection.execute(schemas.CLASS_MEMBERSHIPS)
    connection.execute(schemas.CLASS_JOIN_REQUESTS)
    connection.execute(
        "INSERT INTO teaching_classes (id, name, owner_teacher_id, join_policy, member_count, created_at, updated_at) "
        "VALUES ('class-01', '数学一班', 'teacher-01', 'approval', 0, 1000, 1000)"
    )
    connection.execute(
        "INSERT INTO teaching_classes (id, name, owner_teacher_id, join_policy, member_count, created_at, updated_at) "
        "VALUES ('class-02', '物理二班', 'teacher-02', 'free', 0, 1000, 1000)"
    )
    connection.commit()
    return connection


# ═══════════════════════════════════════════════════════════════════════
#  TeachingClassAccess 测试
# ═══════════════════════════════════════════════════════════════════════


class TestTeachingClassAccess:

    # ── require_owned_class ───────────────────────────────────────

    class TestRequireOwnedClass:

        def test_教师拥有班级_返回该行(self, conn: sqlite3.Connection, access: TeachingClassAccess, teacher: UserView) -> None:
            """教师拥有该班级 → 返回 sqlite3.Row, id 匹配"""
            row = access.require_owned_class(conn, "class-01", teacher)
            assert row is not None
            assert row["id"] == "class-01"

        def test_教师不拥有班级_抛404(self, conn: sqlite3.Connection, access: TeachingClassAccess, teacher: UserView) -> None:
            """教师不是班级 owner → 抛 BusinessError 404 RESOURCE_NOT_FOUND"""
            with pytest.raises(BusinessError) as exc:
                access.require_owned_class(conn, "class-02", teacher)
            assert exc.value.status_code == 404
            assert exc.value.code == "RESOURCE_NOT_FOUND"

        def test_班级不存在_抛404(self, conn: sqlite3.Connection, access: TeachingClassAccess, teacher: UserView) -> None:
            """班级ID不存在 → 抛 BusinessError 404 RESOURCE_NOT_FOUND"""
            with pytest.raises(BusinessError) as exc:
                access.require_owned_class(conn, "class-nonexistent", teacher)
            assert exc.value.status_code == 404
            assert exc.value.code == "RESOURCE_NOT_FOUND"

    # ── require_membership ────────────────────────────────────────

    class TestRequireMembership:

        def test_学习者是成员_返回None(self, conn: sqlite3.Connection, access: TeachingClassAccess) -> None:
            """学习者已是成员 → 返回 None"""
            conn.execute(
                "INSERT INTO class_memberships (class_id, learner_id, created_at) VALUES ('class-01', 'learner-01', 1000)"
            )
            conn.commit()
            result = access.require_membership(conn, "class-01", "learner-01", message="需要成员身份")
            assert result is None

        def test_学习者不是成员_抛403(self, conn: sqlite3.Connection, access: TeachingClassAccess) -> None:
            """学习者不是成员 → 抛 BusinessError 403 CLASS_MEMBERSHIP_REQUIRED"""
            with pytest.raises(BusinessError) as exc:
                access.require_membership(conn, "class-01", "learner-01", message="需要成员身份")
            assert exc.value.status_code == 403
            assert exc.value.code == "CLASS_MEMBERSHIP_REQUIRED"
            assert exc.value.message == "需要成员身份"

    # ── require_membership_or_not_found ────────────────────────────

    class TestRequireMembershipOrNotFound:

        def test_学习者是成员_返回None(self, conn: sqlite3.Connection, access: TeachingClassAccess) -> None:
            """学习者已是成员 → 返回 None"""
            conn.execute(
                "INSERT INTO class_memberships (class_id, learner_id, created_at) VALUES ('class-01', 'learner-01', 1000)"
            )
            conn.commit()
            result = access.require_membership_or_not_found(
                conn, "class-01", "learner-01", code="CLASS_NOT_FOUND", message="班级不存在"
            )
            assert result is None

        def test_学习者不是成员_抛自定义404(self, conn: sqlite3.Connection, access: TeachingClassAccess) -> None:
            """学习者不是成员 → 抛 BusinessError 404 带自定义 code"""
            with pytest.raises(BusinessError) as exc:
                access.require_membership_or_not_found(
                    conn, "class-01", "learner-01", code="CLASS_NOT_FOUND", message="班级不存在"
                )
            assert exc.value.status_code == 404
            assert exc.value.code == "CLASS_NOT_FOUND"
            assert exc.value.message == "班级不存在"

    # ── require_owned_join_request ─────────────────────────────────

    class TestRequireOwnedJoinRequest:

        def test_教师拥有该申请_返回行(self, conn: sqlite3.Connection, access: TeachingClassAccess, teacher: UserView) -> None:
            """教师拥有该 join request → 返回 Row 含 class_id, learner_id, status"""
            conn.execute(
                "INSERT INTO class_join_requests (id, class_id, learner_id, status, created_at) "
                "VALUES ('req-01', 'class-01', 'learner-01', 'pending', 1000)"
            )
            conn.commit()
            row = access.require_owned_join_request(conn, "req-01", teacher)
            assert row["id"] == "req-01"
            assert row["class_id"] == "class-01"
            assert row["learner_id"] == "learner-01"
            assert row["status"] == "pending"

        def test_申请不属于教师_抛404(self, conn: sqlite3.Connection, access: TeachingClassAccess, teacher: UserView) -> None:
            """申请属于其他教师的班级 → 抛 BusinessError 404 RESOURCE_NOT_FOUND"""
            conn.execute(
                "INSERT INTO class_join_requests (id, class_id, learner_id, status, created_at) "
                "VALUES ('req-02', 'class-02', 'learner-01', 'pending', 1000)"
            )
            conn.commit()
            with pytest.raises(BusinessError) as exc:
                access.require_owned_join_request(conn, "req-02", teacher)
            assert exc.value.status_code == 404
            assert exc.value.code == "RESOURCE_NOT_FOUND"

        def test_申请不存在_抛404(self, conn: sqlite3.Connection, access: TeachingClassAccess, teacher: UserView) -> None:
            """request_id 不存在 → 抛 BusinessError 404 RESOURCE_NOT_FOUND"""
            with pytest.raises(BusinessError) as exc:
                access.require_owned_join_request(conn, "req-nonexistent", teacher)
            assert exc.value.status_code == 404
            assert exc.value.code == "RESOURCE_NOT_FOUND"


# ═══════════════════════════════════════════════════════════════════════
#  TeachingClassAdmission 测试
# ═══════════════════════════════════════════════════════════════════════


@pytest.fixture
def admission(access: TeachingClassAccess) -> TeachingClassAdmission:
    return TeachingClassAdmission(access, now_provider=lambda: 2000)


class TestTeachingClassAdmission:

    # ── establish_membership ───────────────────────────────────────

    class TestEstablishMembership:

        def test_新成员_插入成功(self, conn: sqlite3.Connection, admission: TeachingClassAdmission) -> None:
            """学习者不在班级中 → is_new_member=True, joined_at==2000"""
            result = admission.establish_membership(conn, "class-01", "learner-01", reason="join_request_approved")
            assert result.is_new_member is True
            assert result.joined_at == 2000
            # 验证持久化
            row = conn.execute(
                "SELECT 1 FROM class_memberships WHERE class_id='class-01' AND learner_id='learner-01'"
            ).fetchone()
            assert row is not None

        def test_已存在成员_不做插入(self, conn: sqlite3.Connection, admission: TeachingClassAdmission) -> None:
            """学习者已是成员 → is_new_member=False, joined_at 为原始时间 1000"""
            conn.execute(
                "INSERT INTO class_memberships (class_id, learner_id, created_at) VALUES ('class-01', 'learner-01', 1000)"
            )
            conn.commit()
            result = admission.establish_membership(conn, "class-01", "learner-01", reason="duplicate")
            assert result.is_new_member is False
            assert result.joined_at == 1000  # 保留原始时间

        def test_不同班级互不干扰(self, conn: sqlite3.Connection, admission: TeachingClassAdmission) -> None:
            """learner-01 在 class-01 是新人, 在 class-02 也是新人"""
            r1 = admission.establish_membership(conn, "class-01", "learner-01", reason="r1")
            r2 = admission.establish_membership(conn, "class-02", "learner-01", reason="r2")
            assert r1.is_new_member is True
            assert r2.is_new_member is True
            assert r1.joined_at == 2000
            assert r2.joined_at == 2000

    # ── resolve_pending_request ────────────────────────────────────

    class TestResolvePendingRequest:

        @pytest.fixture(autouse=True)
        def _seed_request(self, conn: sqlite3.Connection) -> None:
            """给 class-01（teacher-01 所有）塞一条 pending 申请。"""
            conn.execute(
                "INSERT INTO class_join_requests (id, class_id, learner_id, status, created_at) "
                "VALUES ('req-01', 'class-01', 'learner-01', 'pending', 1500)"
            )
            conn.commit()

        def test_批准通过_创建成员(self, conn: sqlite3.Connection, admission: TeachingClassAdmission, teacher: UserView) -> None:
            """approved → membership_created=True, 状态变为 approved, 成员表有记录"""
            decision = ResolveJoinRequestRequest(status=JoinRequestStatus.APPROVED)
            resp = admission.resolve_pending_request(conn, "req-01", decision, teacher)

            assert resp.request_id == "req-01"
            assert resp.class_id == "class-01"
            assert resp.learner_id == "learner-01"
            assert resp.status == JoinRequestStatus.APPROVED
            assert resp.resolved_at == 2000
            assert resp.resolved_by_teacher_id == "teacher-01"
            assert resp.membership_created is True

            # 验证数据库
            req_row = conn.execute(
                "SELECT status, resolved_at, resolved_by_teacher_id FROM class_join_requests WHERE id='req-01'"
            ).fetchone()
            assert req_row["status"] == "approved"
            assert req_row["resolved_at"] == 2000
            assert req_row["resolved_by_teacher_id"] == "teacher-01"

            member_row = conn.execute(
                "SELECT 1 FROM class_memberships WHERE class_id='class-01' AND learner_id='learner-01'"
            ).fetchone()
            assert member_row is not None

        def test_拒绝通过_不创建成员(self, conn: sqlite3.Connection, admission: TeachingClassAdmission, teacher: UserView) -> None:
            """rejected → membership_created=False, 成员表无记录"""
            decision = ResolveJoinRequestRequest(status=JoinRequestStatus.REJECTED)
            resp = admission.resolve_pending_request(conn, "req-01", decision, teacher)

            assert resp.status == JoinRequestStatus.REJECTED
            assert resp.membership_created is False

            member_row = conn.execute(
                "SELECT 1 FROM class_memberships WHERE class_id='class-01' AND learner_id='learner-01'"
            ).fetchone()
            assert member_row is None

        def test_申请人非pending状态_抛400(self, conn: sqlite3.Connection, admission: TeachingClassAdmission, teacher: UserView) -> None:
            """申请已被处理（非 pending）→ 抛 BusinessError 400 REQUEST_ALREADY_RESOLVED"""
            conn.execute(
                "UPDATE class_join_requests SET status='approved', resolved_at=1700, resolved_by_teacher_id='teacher-01' "
                "WHERE id='req-01'"
            )
            conn.commit()

            decision = ResolveJoinRequestRequest(status=JoinRequestStatus.APPROVED)
            with pytest.raises(BusinessError) as exc:
                admission.resolve_pending_request(conn, "req-01", decision, teacher)
            assert exc.value.status_code == 400
            assert exc.value.code == "REQUEST_ALREADY_RESOLVED"

        def test_批准时学习者是已有成员_成员不重复创建(self, conn: sqlite3.Connection, admission: TeachingClassAdmission, teacher: UserView) -> None:
            """学习者已是成员 → approved 后 membership_created=False, joined_at 不变"""
            conn.execute(
                "INSERT INTO class_memberships (class_id, learner_id, created_at) VALUES ('class-01', 'learner-01', 1000)"
            )
            conn.commit()

            decision = ResolveJoinRequestRequest(status=JoinRequestStatus.APPROVED)
            resp = admission.resolve_pending_request(conn, "req-01", decision, teacher)

            assert resp.membership_created is False

            rows = conn.execute(
                "SELECT COUNT(*) AS cnt FROM class_memberships WHERE class_id='class-01' AND learner_id='learner-01'"
            ).fetchone()
            assert rows["cnt"] == 1  # 没有重复插入
