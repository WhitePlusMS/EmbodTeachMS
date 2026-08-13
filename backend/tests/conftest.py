"""测试共享 seam：用与生产相同的公开 Database 对象播种/检查数据。

测试需要越过 HTTP 直接构造前置状态或检查行数据时，一律通过 build_app
返回的 database（app.database.Database，公开且稳定的对象）打开连接，
不得再戳 app.state.* 模块的私有 _database；能走真实 HTTP 路径构造的
状态优先走 HTTP（interface 才是测试表面）。
"""

from pathlib import Path
import json
import time
import sqlite3

from fastapi import FastAPI

from app.database import Database
from app.main import create_app


def build_app(database_path: Path, **kwargs) -> tuple[FastAPI, Database]:
    """创建应用并返回 (app, database)；两者指向同一个 SQLite 文件。

    database 是测试侧的播种/检查 seam，与生产代码共用同一份 DDL 与连接约束。
    其余关键字参数原样透传给 create_app。
    """
    database = Database(database_path)
    app = create_app(database_path=database.path, **kwargs)
    return app, database


def seed_preparation_state(
    connection: sqlite3.Connection,
    session_id: str,
    *,
    segments: list[tuple[int, str, str]] | None = None,
    highlights: list[dict[str, object]] | None = None,
    questions: list[dict[str, object]] | None = None,
    parse_status: str = "completed",
    current_step: str = "questioning",
    published_at: int | None = None,
) -> None:
    """通过 v4 关系表播种备课状态，避免测试依赖已删除的 JSON 大字段。"""
    now = int(time.time())
    connection.executemany(
        """
        INSERT INTO preparation_session_segments(
            session_id, ordinal, document_id, chunk_id, document_version,
            block_type, content, created_at
        ) VALUES (?, ?, NULL, NULL, NULL, ?, ?, ?)
        """,
        [(session_id, ordinal, block_type, content, now) for ordinal, block_type, content in (segments or [])],
    )
    connection.executemany(
        """
        INSERT INTO preparation_highlights(
            id, session_id, segment_ordinal, start_offset, end_offset, created_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                str(item["id"]),
                session_id,
                int(item["paragraphOrdinal"]),
                int(item["startOffset"]),
                int(item["endOffset"]),
                int(item.get("createdAt", now)),
            )
            for item in (highlights or [])
        ],
    )
    connection.executemany(
        """
        INSERT INTO preparation_questions(
            id, session_id, source, review_status, question_type, stem,
            options_json, correct_answers_json, knowledge_points_json,
            highlight_source_ids_json, hint, explanation, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                str(item["id"]),
                session_id,
                str(item.get("source", "manual")),
                str(item.get("review_status", "confirmed")),
                str(item.get("type", "single_choice")),
                str(item.get("stem", "测试题目")),
                json.dumps(item.get("options", []), ensure_ascii=False),
                json.dumps(item.get("answers", []), ensure_ascii=False),
                json.dumps(item.get("knowledge_points", []), ensure_ascii=False),
                json.dumps(item.get("highlight_source_ids", []), ensure_ascii=False),
                str(item.get("hint", "")),
                str(item.get("explanation", "")),
                int(item.get("created_at", now)),
                int(item.get("updated_at", now)),
            )
            for item in (questions or [])
        ],
    )
    connection.execute(
        """
        UPDATE preparation_sessions
        SET parse_status = ?, current_step = ?, published_at = ?, updated_at = ?
        WHERE id = ?
        """,
        (parse_status, current_step, published_at, now, session_id),
    )
