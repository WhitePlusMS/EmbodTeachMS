import logging
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass

from app.auth.models import UserView
from app.common.errors import BusinessError
from app.teaching_classes.access import TeachingClassAccess
from app.teaching_classes.models import (
    JoinRequestStatus,
    ResolveJoinRequestRequest,
    ResolveJoinRequestResponse,
)

logger = logging.getLogger("course_agent.teaching_classes")


@dataclass(frozen=True)
class MembershipAdmission:
    """教学班准入建立成员关系后的确定性结果。"""

    joined_at: int
    is_new_member: bool


class TeachingClassAdmission:
    """将申请终态与成员关系的原子迁移收进单一 module。"""

    def __init__(self, access: TeachingClassAccess, now_provider: Callable[[], int]) -> None:
        self._access = access
        self._now = now_provider

    def establish_membership(
        self,
        connection: sqlite3.Connection,
        class_id: str,
        learner_id: str,
        reason: str,
    ) -> MembershipAdmission:
        """以成员主键为唯一事实建立教学班准入，统一全部正式成员迁移。"""
        now = self._now()
        inserted = connection.execute(
            """
            INSERT OR IGNORE INTO class_memberships (class_id, learner_id, created_at)
            VALUES (?, ?, ?)
            """,
            (class_id, learner_id, now),
        )
        membership = connection.execute(
            """
            SELECT created_at FROM class_memberships
            WHERE class_id = ? AND learner_id = ?
            """,
            (class_id, learner_id),
        ).fetchone()
        is_new_member = inserted.rowcount == 1

        if is_new_member:
            logger.info(
                "class_membership_created class_id=%s learner_id=%s reason=%s",
                class_id,
                learner_id,
                reason,
            )

        return MembershipAdmission(
            joined_at=membership["created_at"],
            is_new_member=is_new_member,
        )

    def resolve_pending_request(
        self,
        connection: sqlite3.Connection,
        request_id: str,
        decision: ResolveJoinRequestRequest,
        teacher: UserView,
    ) -> ResolveJoinRequestResponse:
        request = self._access.require_owned_join_request(connection, request_id, teacher)
        now = self._now()
        updated = connection.execute(
            """
            UPDATE class_join_requests
            SET status = ?, resolved_at = ?, resolved_by_teacher_id = ?
            WHERE id = ? AND status = ?
            """,
            (decision.status.value, now, teacher.id, request_id, JoinRequestStatus.PENDING.value),
        )
        if updated.rowcount != 1:
            raise BusinessError(
                status_code=400,
                code="REQUEST_ALREADY_RESOLVED",
                message="该申请已被处理",
            )

        membership_created = False
        if decision.status == JoinRequestStatus.APPROVED:
            membership_created = self.establish_membership(
                connection,
                request["class_id"],
                request["learner_id"],
                "join_request_approved",
            ).is_new_member

        return ResolveJoinRequestResponse(
            request_id=request_id,
            class_id=request["class_id"],
            learner_id=request["learner_id"],
            status=decision.status,
            resolved_at=now,
            resolved_by_teacher_id=teacher.id,
            membership_created=membership_created,
        )
