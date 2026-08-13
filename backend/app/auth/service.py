import sqlite3
import logging
import uuid
from collections.abc import Callable

from app.auth.models import (
    AuthPayload,
    LoginRequest,
    RegisterRequest,
    UserRole,
    UserView,
)
from app.auth.security import (
    TokenClaims,
    decode_token,
    hash_password,
    issue_token,
    verify_password,
)
from app.common.errors import BusinessError
from app.database import Database


SESSION_DURATION_SECONDS = 8 * 60 * 60
logger = logging.getLogger("course_agent.auth")


class AuthService:
    """在一个明确边界内维护账号、会话和令牌的一致性。"""

    def __init__(
        self,
        database: Database,
        jwt_secret: str,
        now_provider: Callable[[], int],
    ) -> None:
        self._database = database
        self._jwt_secret = jwt_secret
        self._now = now_provider

    def register(self, request: RegisterRequest) -> AuthPayload:
        now = self._now()
        user_id = str(uuid.uuid4())
        try:
            with self._database.connect() as connection:
                connection.execute(
                    """
                    INSERT INTO users (
                        id, username, password_hash, display_name, role, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        request.username,
                        hash_password(request.password),
                        request.display_name,
                        request.role.value,
                        now,
                    ),
                )
        except sqlite3.IntegrityError as error:
            raise BusinessError(
                status_code=409,
                code="AUTH_USERNAME_EXISTS",
                message="用户名已存在",
            ) from error

        user = UserView(
            id=user_id,
            username=request.username,
            display_name=request.display_name,
            role=request.role,
        )
        payload = self._create_session(user, now)
        logger.info("user_registered user_id=%s role=%s", user.id, user.role.value)
        return payload

    def login(self, request: LoginRequest) -> AuthPayload:
        with self._database.connect() as connection:
            row = connection.execute(
                """
                SELECT id, username, password_hash, display_name, role
                FROM users
                WHERE username = ?
                """,
                (request.username,),
            ).fetchone()

        if row is None or not verify_password(request.password, row["password_hash"]):
            raise BusinessError(
                status_code=401,
                code="AUTH_INVALID_CREDENTIALS",
                message="用户名或密码错误",
            )

        user = UserView(
            id=row["id"],
            username=row["username"],
            display_name=row["display_name"],
            role=UserRole(row["role"]),
        )
        payload = self._create_session(user, self._now())
        logger.info("user_logged_in user_id=%s role=%s", user.id, user.role.value)
        return payload

    def authenticate(self, token: str) -> UserView:
        user, _ = self._authenticate(token)
        return user

    def logout(self, token: str) -> None:
        """撤销当前 JWT 对应的服务端会话，使旧令牌立即失效。"""
        user, claims = self._authenticate(token)

        with self._database.connect() as connection:
            result = connection.execute(
                """
                UPDATE sessions
                SET revoked_at = ?
                WHERE id = ? AND revoked_at IS NULL
                """,
                (self._now(), claims.session_id),
            )
        if result.rowcount != 1:
            self._raise_invalid_session()
        logger.info(
            "session_revoked user_id=%s role=%s",
            user.id,
            user.role.value,
        )

    def _authenticate(self, token: str) -> tuple[UserView, TokenClaims]:
        """单次解码令牌并校验服务端会话，返回用户视图与令牌声明。"""
        claims = decode_token(token, self._jwt_secret)
        now = self._now()
        if claims is None or claims.expires_at <= now:
            self._raise_invalid_session()

        with self._database.connect() as connection:
            row = connection.execute(
                """
                SELECT
                    users.id,
                    users.username,
                    users.display_name,
                    users.role,
                    sessions.expires_at,
                    sessions.revoked_at
                FROM sessions
                JOIN users ON users.id = sessions.user_id
                WHERE sessions.id = ? AND users.id = ?
                """,
                (claims.session_id, claims.user_id),
            ).fetchone()

        if (
            row is None
            or row["revoked_at"] is not None
            or row["expires_at"] <= now
            or row["role"] != claims.role.value
        ):
            self._raise_invalid_session()

        return UserView(
            id=row["id"],
            username=row["username"],
            display_name=row["display_name"],
            role=UserRole(row["role"]),
        ), claims

    def _create_session(self, user: UserView, now: int) -> AuthPayload:
        session_id = str(uuid.uuid4())
        expires_at = now + SESSION_DURATION_SECONDS
        with self._database.connect() as connection:
            # 惰性清理已过期会话，避免 sessions 表无限增长
            connection.execute(
                "DELETE FROM sessions WHERE expires_at <= ?",
                (now,),
            )
            connection.execute(
                """
                INSERT INTO sessions (id, user_id, expires_at)
                VALUES (?, ?, ?)
                """,
                (session_id, user.id, expires_at),
            )

        logger.info("session_created user_id=%s role=%s", user.id, user.role.value)
        token = issue_token(
            TokenClaims(
                session_id=session_id,
                user_id=user.id,
                role=user.role,
                expires_at=expires_at,
            ),
            self._jwt_secret,
        )
        return AuthPayload(user=user, access_token=token)

    @staticmethod
    def _raise_invalid_session() -> None:
        raise BusinessError(
            status_code=401,
            code="AUTH_SESSION_INVALID",
            message="登录状态已失效，请重新登录",
        )
