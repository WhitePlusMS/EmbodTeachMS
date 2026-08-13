from pathlib import Path

from app.auth.models import LoginRequest, RegisterRequest, UserRole
from app.auth.service import SESSION_DURATION_SECONDS, AuthService
from app.database import Database


def test_expired_sessions_are_cleaned_up_on_next_sign_in(tmp_path: Path) -> None:
    """过期会话在下一次登录时被惰性清理，sessions 表不会无限增长。"""
    database = Database(tmp_path / "cleanup.db")
    database.initialize()
    current_time = [1_000_000]
    service = AuthService(
        database,
        "test-secret-with-enough-length",
        lambda: current_time[0],
    )

    service.register(
        RegisterRequest(
            username="cleanup_user",
            password="StrongPass123!",
            display_name="清理",
            role=UserRole.LEARNER,
        )
    )
    current_time[0] += SESSION_DURATION_SECONDS + 1

    service.login(
        LoginRequest(username="cleanup_user", password="StrongPass123!")
    )

    with database.connect() as connection:
        count = connection.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    assert count == 1
