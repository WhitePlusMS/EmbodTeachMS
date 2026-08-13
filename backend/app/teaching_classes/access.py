import sqlite3

from app.auth.models import UserView
from app.common.errors import BusinessError


class TeachingClassAccess:
    """集中教学班准入规则：教师资源归属、学习者成员校验与隐藏存在性。"""

    def require_owned_class(
        self, connection: sqlite3.Connection, class_id: str, teacher: UserView
    ) -> sqlite3.Row:
        row = connection.execute(
            "SELECT id FROM teaching_classes WHERE id = ? AND owner_teacher_id = ?",
            (class_id, teacher.id),
        ).fetchone()
        if row is None:
            raise BusinessError(
                status_code=404, code="RESOURCE_NOT_FOUND", message="教学班不存在"
            )
        return row

    def require_membership(
        self,
        connection: sqlite3.Connection,
        class_id: str,
        learner_id: str,
        *,
        message: str,
    ) -> None:
        """校验学习者是教学班正式成员，否则抛出 403。"""
        row = connection.execute(
            "SELECT 1 FROM class_memberships WHERE class_id = ? AND learner_id = ?",
            (class_id, learner_id),
        ).fetchone()
        if row is None:
            raise BusinessError(
                status_code=403, code="CLASS_MEMBERSHIP_REQUIRED", message=message
            )

    def require_membership_or_not_found(
        self,
        connection: sqlite3.Connection,
        class_id: str,
        learner_id: str,
        *,
        code: str,
        message: str,
    ) -> None:
        """成员校验但对外隐藏存在性，非成员抛出 404。"""
        row = connection.execute(
            "SELECT 1 FROM class_memberships WHERE class_id = ? AND learner_id = ?",
            (class_id, learner_id),
        ).fetchone()
        if row is None:
            raise BusinessError(status_code=404, code=code, message=message)

    def require_owned_join_request(
        self, connection: sqlite3.Connection, request_id: str, teacher: UserView
    ) -> sqlite3.Row:
        row = connection.execute(
            """
            SELECT cjr.id, cjr.class_id, cjr.learner_id, cjr.status
            FROM class_join_requests cjr
            JOIN teaching_classes tc ON tc.id = cjr.class_id
            WHERE cjr.id = ? AND tc.owner_teacher_id = ?
            """,
            (request_id, teacher.id),
        ).fetchone()
        if row is None:
            raise BusinessError(
                status_code=404, code="RESOURCE_NOT_FOUND", message="申请不存在"
            )
        return row
