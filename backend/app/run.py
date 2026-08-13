import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from app.llm_gateway import create_configured_chat_gateway
from app.main import create_app


def _required_jwt_secret() -> str:
    secret = os.environ.get("COURSE_AGENT_JWT_SECRET", "")
    if len(secret) < 32:
        raise RuntimeError("COURSE_AGENT_JWT_SECRET 必须至少包含 32 个字符")
    return secret


def _allowed_origins() -> tuple[str, ...]:
    raw_origins = os.environ.get(
        "COURSE_AGENT_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173",
    )
    return tuple(origin.strip() for origin in raw_origins.split(",") if origin.strip())


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
load_dotenv()

app = create_app(
    database_path=Path(
        os.environ.get("COURSE_AGENT_DATABASE_PATH", "data/course-agent.db")
    ),
    jwt_secret=_required_jwt_secret(),
    allowed_origins=_allowed_origins(),
    chat_gateway=create_configured_chat_gateway(),
)
