import json
import logging
import secrets
import sqlite3
import string
import uuid
from collections.abc import Callable

from app.auth.models import UserView
from app.common.errors import BusinessError
from app.database import Database
from app.llm_gateway import (
    ChatGateway,
    UnconfiguredChatGateway,
)
from app.teaching_classes.access import TeachingClassAccess
from app.teaching_classes.admission import TeachingClassAdmission
from app.teaching_classes.course_overview import CourseOverviewModule
from app.teaching_classes.content_query import PublishedContentQuery
from app.teaching_classes.models import (
    AuthorizationCodeView,
    CreateJoinRequestResponse,
    CreateTeachingClassRequest,
    CreateOrUpdateAuthorizationCodeRequest,
    DiscoverableClassView,
    JoinByAuthorizationCodeRequest,
    JoinClassResponse,
    JoinPolicy,
    JoinRequestListView,
    JoinRequestStatus,
    JoinRequestView,
    ResolveJoinRequestRequest,
    ResolveJoinRequestResponse,
    TeachingClassView,
    UpdateJoinPolicyRequest,
    CourseOverview,
    CourseOverviewCandidateView,
    UpdateCourseOverviewRequest,
    PublishedContentView,
    PublishedContentListView,
    PublishedContentDetailView,
    TeacherPublishedContentListView,
    CourseContentCompletionView,
    MarkContentCompleteRequest,
    CourseHomeSummaryView,
)
from app.teaching_classes.practice import PracticeModule


logger = logging.getLogger("course_agent.teaching_classes")


class TeachingClassService:
    """教学班管理服务"""

    def __init__(
        self,
        database: Database,
        now_provider: Callable[[], int],
        practice: PracticeModule,
        chat_gateway: ChatGateway | None = None,
        course_overview: CourseOverviewModule | None = None,
        content_query: PublishedContentQuery | None = None,
    ) -> None:
        self._database = database
        self._now = now_provider
        self._access = TeachingClassAccess()
        self._admission = TeachingClassAdmission(self._access, now_provider)
        self._practice = practice
        self._chat_gateway: ChatGateway = chat_gateway or UnconfiguredChatGateway()

        # 接受外部注入的子模块，否则自动创建
        self._course_overview = course_overview or CourseOverviewModule(database, now_provider, chat_gateway)
        self._content_query = content_query or PublishedContentQuery(database, now_provider, practice)

    def create_class(
        self, request: CreateTeachingClassRequest, teacher: UserView
    ) -> TeachingClassView:
        """创建教学班"""
        # 名称验证由 Pydantic 处理
        name = request.name

        now = self._now()
        class_id = str(uuid.uuid4())

        with self._database.connect() as connection:
            connection.execute(
                """
                INSERT INTO teaching_classes (
                    id, name, join_policy, owner_teacher_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (class_id, name, request.join_policy.value, teacher.id, now, now),
            )

        logger.info(
            "teaching_class_created class_id=%s teacher_id=%s join_policy=%s",
            class_id,
            teacher.id,
            request.join_policy.value,
        )

        return TeachingClassView(
            id=class_id,
            name=name,
            join_policy=request.join_policy,
            member_count=0,
            created_at=now,
            updated_at=now,
        )

    def list_teacher_classes(self, teacher: UserView) -> list[TeachingClassView]:
        """获取教师的教学班列表"""
        with self._database.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    tc.id,
                    tc.name,
                    tc.join_policy,
                    tc.created_at,
                    tc.updated_at,
                    COUNT(cm.learner_id) as member_count
                FROM teaching_classes tc
                LEFT JOIN class_memberships cm ON tc.id = cm.class_id
                WHERE tc.owner_teacher_id = ?
                GROUP BY tc.id
                ORDER BY tc.updated_at DESC
                """,
                (teacher.id,),
            ).fetchall()

        return [
            TeachingClassView(
                id=row["id"],
                name=row["name"],
                join_policy=JoinPolicy(row["join_policy"]),
                member_count=row["member_count"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def get_class_by_id(
        self, class_id: str, teacher: UserView
    ) -> TeachingClassView:
        """根据ID获取教学班详情"""
        with self._database.connect() as connection:
            row = connection.execute(
                """
                SELECT
                    tc.id,
                    tc.name,
                    tc.join_policy,
                    tc.created_at,
                    tc.updated_at,
                    COUNT(cm.learner_id) as member_count
                FROM teaching_classes tc
                LEFT JOIN class_memberships cm ON tc.id = cm.class_id
                WHERE tc.id = ? AND tc.owner_teacher_id = ?
                GROUP BY tc.id
                """,
                (class_id, teacher.id),
            ).fetchone()

        if row is None:
            raise BusinessError(
                status_code=404,
                code="RESOURCE_NOT_FOUND",
                message="教学班不存在",
            )

        return TeachingClassView(
            id=row["id"],
            name=row["name"],
            join_policy=JoinPolicy(row["join_policy"]),
            member_count=row["member_count"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def discover_classes(self, learner: UserView) -> list[DiscoverableClassView]:
        """学习者发现可加入的教学班（排除closed状态）"""
        with self._database.connect() as connection:
            # 获取所有非closed状态的教学班，并检查学习者是否已是成员
            rows = connection.execute(
                """
                SELECT
                    tc.id,
                    tc.name,
                    tc.join_policy,
                    tc.created_at,
                    tc.updated_at,
                    COUNT(cm.learner_id) as member_count,
                    EXISTS(
                        SELECT 1 FROM class_memberships
                        WHERE class_id = tc.id AND learner_id = ?
                    ) as is_member
                FROM teaching_classes tc
                LEFT JOIN class_memberships cm ON tc.id = cm.class_id
                WHERE tc.join_policy != ?
                GROUP BY tc.id
                ORDER BY tc.updated_at DESC
                """,
                (learner.id, JoinPolicy.CLOSED.value),
            ).fetchall()

        return [
            DiscoverableClassView(
                id=row["id"],
                name=row["name"],
                join_policy=JoinPolicy(row["join_policy"]),
                member_count=row["member_count"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                is_member=bool(row["is_member"]),
            )
            for row in rows
        ]

    def list_learner_classes(self, learner: UserView) -> list[TeachingClassView]:
        """返回学习者已经正式加入的教学班，不受当前加入状态影响。"""
        with self._database.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    tc.id,
                    tc.name,
                    tc.join_policy,
                    tc.created_at,
                    tc.updated_at,
                    COUNT(all_members.learner_id) AS member_count
                FROM class_memberships learner_membership
                JOIN teaching_classes tc ON tc.id = learner_membership.class_id
                LEFT JOIN class_memberships all_members ON all_members.class_id = tc.id
                WHERE learner_membership.learner_id = ?
                GROUP BY tc.id
                ORDER BY tc.updated_at DESC
                """,
                (learner.id,),
            ).fetchall()

        return [
            TeachingClassView(
                id=row["id"],
                name=row["name"],
                join_policy=JoinPolicy(row["join_policy"]),
                member_count=row["member_count"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def join_class(self, class_id: str, learner: UserView) -> JoinClassResponse:
        """学习者加入教学班"""
        with self._database.connect() as connection:
            # 验证教学班存在且不是closed状态
            class_row = connection.execute(
                """
                SELECT id, join_policy
                FROM teaching_classes
                WHERE id = ?
                """,
                (class_id,),
            ).fetchone()

            if class_row is None:
                raise BusinessError(
                    status_code=404,
                    code="RESOURCE_NOT_FOUND",
                    message="教学班不存在",
                )

            join_policy = JoinPolicy(class_row["join_policy"])

            # 检查加入策略
            if join_policy == JoinPolicy.CLOSED:
                raise BusinessError(
                    status_code=403,
                    code="CLASS_JOIN_FORBIDDEN",
                    message="该教学班已关闭加入",
                )

            if join_policy == JoinPolicy.APPROVAL:
                raise BusinessError(
                    status_code=403,
                    code="CLASS_JOIN_APPROVAL_REQUIRED",
                    message="该教学班需要申请加入，不能直接加入",
                )

            membership = self._admission.establish_membership(
                connection,
                class_id,
                learner.id,
                "free_join",
            )

            return JoinClassResponse(
                class_id=class_id,
                learner_id=learner.id,
                joined_at=membership.joined_at,
                is_new_member=membership.is_new_member,
            )

    def create_join_request(self, class_id: str, learner: UserView) -> CreateJoinRequestResponse:
        """学习者申请加入需要审批的教学班"""
        now = self._now()

        with self._database.connect() as connection:
            # 验证教学班存在且是approval策略
            class_row = connection.execute(
                """
                SELECT id, join_policy
                FROM teaching_classes
                WHERE id = ?
                """,
                (class_id,),
            ).fetchone()

            if class_row is None:
                raise BusinessError(
                    status_code=404,
                    code="RESOURCE_NOT_FOUND",
                    message="教学班不存在",
                )

            join_policy = JoinPolicy(class_row["join_policy"])

            if join_policy != JoinPolicy.APPROVAL:
                raise BusinessError(
                    status_code=400,
                    code="INVALID_JOIN_REQUEST",
                    message="该教学班不需要申请加入",
                )

            # 检查是否已经是成员
            membership_exists = connection.execute(
                """
                SELECT 1 FROM class_memberships
                WHERE class_id = ? AND learner_id = ?
                """,
                (class_id, learner.id),
            ).fetchone()

            if membership_exists:
                raise BusinessError(
                    status_code=400,
                    code="ALREADY_MEMBER",
                    message="您已经是该教学班的成员",
                )

            # 检查是否已有申请。申请表按班级和学习者唯一保留一条记录，
            # 被拒绝的记录重新置为pending即可支持学习者再次申请。
            existing_request = connection.execute(
                """
                SELECT id, status FROM class_join_requests
                WHERE class_id = ? AND learner_id = ?
                """,
                (class_id, learner.id),
            ).fetchone()

            if existing_request:
                if existing_request["status"] == JoinRequestStatus.PENDING:
                    raise BusinessError(
                        status_code=400,
                        code="PENDING_REQUEST_EXISTS",
                        message="您已经提交了加入申请，请等待审批",
                    )
                if existing_request["status"] == JoinRequestStatus.REJECTED:
                    reopened_request = connection.execute(
                        """
                        UPDATE class_join_requests
                        SET status = ?, created_at = ?, resolved_at = NULL,
                            resolved_by_teacher_id = NULL
                        WHERE id = ? AND status = ?
                        """,
                        (
                            JoinRequestStatus.PENDING.value,
                            now,
                            existing_request["id"],
                            JoinRequestStatus.REJECTED.value,
                        ),
                    )
                    if reopened_request.rowcount == 1:
                        logger.info(
                            "join_request_reopened request_id=%s class_id=%s learner_id=%s",
                            existing_request["id"],
                            class_id,
                            learner.id,
                        )
                        return CreateJoinRequestResponse(
                            request_id=existing_request["id"],
                            class_id=class_id,
                            learner_id=learner.id,
                            status=JoinRequestStatus.PENDING,
                            created_at=now,
                            is_new_request=True,
                        )

                    raise BusinessError(
                        status_code=400,
                        code="PENDING_REQUEST_EXISTS",
                        message="您已经提交了加入申请，请等待审批",
                    )

                raise BusinessError(
                    status_code=400,
                    code="REQUEST_ALREADY_RESOLVED",
                    message="您的申请已被处理，请查看结果",
                )

            # 创建申请（唯一约束 UNIQUE(class_id, learner_id) 兜底并发竞态）
            request_id = str(uuid.uuid4())
            insert_result = connection.execute(
                """
                INSERT OR IGNORE INTO class_join_requests (
                    id, class_id, learner_id, status, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (request_id, class_id, learner.id, JoinRequestStatus.PENDING.value, now),
            )

            is_new_request = insert_result.rowcount == 1
            if not is_new_request:
                # 并发下已有其他请求抢先创建，按已有 pending 申请处理
                raise BusinessError(
                    status_code=400,
                    code="PENDING_REQUEST_EXISTS",
                    message="您已经提交了加入申请，请等待审批",
                )

            logger.info(
                "join_request_created request_id=%s class_id=%s learner_id=%s",
                request_id,
                class_id,
                learner.id,
            )

            return CreateJoinRequestResponse(
                request_id=request_id,
                class_id=class_id,
                learner_id=learner.id,
                status=JoinRequestStatus.PENDING,
                created_at=now,
                is_new_request=is_new_request,
            )

    def list_pending_join_requests(self, class_id: str, teacher: UserView) -> JoinRequestListView:
        """教师查看待处理的加入申请"""
        with self._database.connect() as connection:
            self._access.require_owned_class(connection, class_id, teacher)

            # 获取待处理申请，包含学习者显示名称
            rows = connection.execute(
                """
                SELECT
                    cjr.id,
                    cjr.class_id,
                    cjr.learner_id,
                    cjr.status,
                    cjr.created_at,
                    cjr.resolved_at,
                    cjr.resolved_by_teacher_id,
                    u.display_name as learner_display_name
                FROM class_join_requests cjr
                JOIN users u ON cjr.learner_id = u.id
                WHERE cjr.class_id = ? AND cjr.status = ?
                ORDER BY cjr.created_at ASC
                """,
                (class_id, JoinRequestStatus.PENDING.value),
            ).fetchall()

        return JoinRequestListView(
            items=[
                JoinRequestView(
                    id=row["id"],
                    class_id=row["class_id"],
                    learner_id=row["learner_id"],
                    status=JoinRequestStatus(row["status"]),
                    created_at=row["created_at"],
                    resolved_at=row["resolved_at"],
                    resolved_by_teacher_id=row["resolved_by_teacher_id"],
                    learner_display_name=row["learner_display_name"],
                )
                for row in rows
            ]
        )

    def resolve_join_request(
        self, request_id: str, request: ResolveJoinRequestRequest, teacher: UserView
    ) -> ResolveJoinRequestResponse:
        """教师审批或拒绝加入申请"""
        with self._database.connect() as connection:
            result = self._admission.resolve_pending_request(
                connection, request_id, request, teacher
            )

            logger.info(
                "join_request_resolved request_id=%s teacher_id=%s status=%s membership_created=%s",
                request_id,
                teacher.id,
                result.status.value,
                result.membership_created,
            )
            return result

    def get_learner_join_requests(self, learner: UserView) -> JoinRequestListView:
        """学习者查看自己的加入申请"""
        with self._database.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    cjr.id,
                    cjr.class_id,
                    cjr.learner_id,
                    cjr.status,
                    cjr.created_at,
                    cjr.resolved_at,
                    cjr.resolved_by_teacher_id,
                    tc.name as class_name
                FROM class_join_requests cjr
                JOIN teaching_classes tc ON cjr.class_id = tc.id
                WHERE cjr.learner_id = ?
                ORDER BY cjr.created_at DESC
                """,
                (learner.id,),
            ).fetchall()

        return JoinRequestListView(
            items=[
                JoinRequestView(
                    id=row["id"],
                    class_id=row["class_id"],
                    learner_id=row["learner_id"],
                    status=JoinRequestStatus(row["status"]),
                    created_at=row["created_at"],
                    resolved_at=row["resolved_at"],
                    resolved_by_teacher_id=row["resolved_by_teacher_id"],
                    class_name=row["class_name"],
                )
                for row in rows
            ]
        )

    def update_join_policy(
        self,
        class_id: str,
        request: UpdateJoinPolicyRequest,
        teacher: UserView,
    ) -> TeachingClassView:
        """更新教学班加入策略"""
        now = self._now()

        with self._database.connect() as connection:
            # 获取当前班级信息，同时验证存在性和所有权
            class_row = connection.execute(
                """
                SELECT id, updated_at
                FROM teaching_classes
                WHERE id = ? AND owner_teacher_id = ?
                """,
                (class_id, teacher.id),
            ).fetchone()

            if class_row is None:
                raise BusinessError(
                    status_code=404,
                    code="RESOURCE_NOT_FOUND",
                    message="教学班不存在",
                )

            # 确保 updated_at 单调递增
            new_updated_at = max(class_row["updated_at"] + 1, now)

            connection.execute(
                """
                UPDATE teaching_classes
                SET join_policy = ?, updated_at = ?
                WHERE id = ? AND owner_teacher_id = ?
                """,
                (request.join_policy.value, new_updated_at, class_id, teacher.id),
            )

            # 获取更新后的完整信息
            row = connection.execute(
                """
                SELECT
                    tc.id,
                    tc.name,
                    tc.join_policy,
                    tc.created_at,
                    tc.updated_at,
                    COUNT(cm.learner_id) as member_count
                FROM teaching_classes tc
                LEFT JOIN class_memberships cm ON tc.id = cm.class_id
                WHERE tc.id = ? AND tc.owner_teacher_id = ?
                GROUP BY tc.id
                """,
                (class_id, teacher.id),
            ).fetchone()

        logger.info(
            "teaching_class_join_policy_updated class_id=%s teacher_id=%s join_policy=%s",
            class_id,
            teacher.id,
            request.join_policy.value,
        )

        return TeachingClassView(
            id=row["id"],
            name=row["name"],
            join_policy=JoinPolicy(row["join_policy"]),
            member_count=row["member_count"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def get_authorization_code(
        self, class_id: str, teacher: UserView
    ) -> AuthorizationCodeView | None:
        """获取教学班的授权码"""
        with self._database.connect() as connection:
            self._access.require_owned_class(connection, class_id, teacher)

            row = connection.execute(
                """
                SELECT id, class_id, code, enabled, expires_at, created_at, updated_at
                FROM class_authorization_codes
                WHERE class_id = ?
                """,
                (class_id,),
            ).fetchone()

            if row is None:
                return None

            return AuthorizationCodeView(
                id=row["id"],
                class_id=row["class_id"],
                code=row["code"],
                enabled=bool(row["enabled"]),
                expires_at=row["expires_at"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def create_or_update_authorization_code(
        self,
        class_id: str,
        request: CreateOrUpdateAuthorizationCodeRequest,
        teacher: UserView,
    ) -> AuthorizationCodeView:
        """创建或更新教学班授权码"""
        now = self._now()

        # 验证过期时间
        if request.expires_at is not None and request.expires_at <= now:
            raise BusinessError(
                status_code=400,
                code="INVALID_EXPIRATION_TIME",
                message="过期时间必须大于当前时间",
            )

        with self._database.connect() as connection:
            self._access.require_owned_class(connection, class_id, teacher)

            # 用 UPSERT 收敛首次保存的 check-then-insert 竞态；未传过期时间时保留已有值。
            connection.execute("BEGIN IMMEDIATE")
            code_id = str(uuid.uuid4())
            code = "".join(
                secrets.choice(string.ascii_uppercase + string.digits)
                for _ in range(12)
            )
            connection.execute(
                """
                INSERT INTO class_authorization_codes (
                    id, class_id, code, enabled, expires_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(class_id) DO UPDATE SET
                    enabled = excluded.enabled,
                    expires_at = COALESCE(excluded.expires_at, class_authorization_codes.expires_at),
                    updated_at = excluded.updated_at
                """,
                (code_id, class_id, code, request.enabled, request.expires_at, now, now),
            )
            row = connection.execute(
                """
                SELECT id, class_id, code, enabled, expires_at, created_at, updated_at
                FROM class_authorization_codes
                WHERE class_id = ?
                """,
                (class_id,),
            ).fetchone()

            logger.info(
                "authorization_code_updated class_id=%s teacher_id=%s enabled=%s",
                class_id,
                teacher.id,
                request.enabled,
            )

            return AuthorizationCodeView(
                id=row["id"],
                class_id=row["class_id"],
                code=row["code"],
                enabled=bool(row["enabled"]),
                expires_at=row["expires_at"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def join_class_by_authorization_code(
        self,
        request: JoinByAuthorizationCodeRequest,
        learner: UserView,
    ) -> JoinClassResponse:
        """通过授权码加入教学班"""
        now = self._now()

        with self._database.connect() as connection:
            # 验证授权码
            auth_code_row = connection.execute(
                """
                SELECT class_id, enabled, expires_at
                FROM class_authorization_codes
                WHERE code = ?
                """,
                (request.code,),
            ).fetchone()

            if auth_code_row is None:
                raise BusinessError(
                    status_code=400,
                    code="CLASS_AUTHORIZATION_CODE_INVALID",
                    message="授权码无效",
                )

            class_id = auth_code_row["class_id"]

            # 检查授权码是否启用
            if not auth_code_row["enabled"]:
                raise BusinessError(
                    status_code=400,
                    code="CLASS_AUTHORIZATION_CODE_INVALID",
                    message="授权码无效",
                )

            # 检查授权码是否过期
            if (
                auth_code_row["expires_at"] is not None
                and auth_code_row["expires_at"] <= now
            ):
                raise BusinessError(
                    status_code=400,
                    code="CLASS_AUTHORIZATION_CODE_INVALID",
                    message="授权码无效",
                )

            # 验证教学班存在
            class_row = connection.execute(
                "SELECT id FROM teaching_classes WHERE id = ?",
                (class_id,),
            ).fetchone()

            if class_row is None:
                raise BusinessError(
                    status_code=404,
                    code="RESOURCE_NOT_FOUND",
                    message="教学班不存在",
                )

            membership = self._admission.establish_membership(
                connection,
                class_id,
                learner.id,
                "authorization_code",
            )

            return JoinClassResponse(
                class_id=class_id,
                learner_id=learner.id,
                joined_at=membership.joined_at,
                is_new_member=membership.is_new_member,
            )

    # ── 委托给子模块（待逐步替换为直连注入） ────────────────────────────

    def get_published_content_detail_for_learner(self, class_id: str, content_id: str, learner: UserView) -> PublishedContentDetailView:
        """被 llm_gateway/router.py 使用，其他路由已直连子模块。"""
        return self._content_query.get_published_content_detail_for_learner(class_id, content_id, learner)
