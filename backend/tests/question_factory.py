"""结构化课程题目的测试数据工厂。"""

import json
import sqlite3
import time
import uuid


def insert_published_question(
    connection: sqlite3.Connection,
    class_id: str,
    *,
    stem: str,
    options: list[str],
    correct_answers: list[int],
    question_type: str = "single_choice",
    explanation: str = "",
    hint: str = "",
    knowledge_points: list[str] | None = None,
    title: str = "测试题目",
    content_id: str | None = None,
    now: int | None = None,
) -> str:
    """按生产 schema 原子插入公开题面与私有判分事实。"""
    question_id = content_id or str(uuid.uuid4())
    created_at = int(time.time()) if now is None else now
    connection.execute(
        """
        INSERT INTO course_contents (
            id, class_id, content_type, publication_status,
            title, content, created_at, updated_at
        ) VALUES (?, ?, 'question', 'published', ?, ?, ?, ?)
        """,
        (question_id, class_id, title, stem, created_at, created_at),
    )
    connection.execute(
        """
        INSERT INTO course_content_questions (
            content_id, question_type, stem, options_json,
            correct_answers_json, knowledge_points_json, hint, explanation
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            question_id,
            question_type,
            stem,
            json.dumps(options, ensure_ascii=False, separators=(",", ":")),
            json.dumps(sorted(correct_answers), separators=(",", ":")),
            json.dumps(knowledge_points or [], ensure_ascii=False, separators=(",", ":")),
            hint,
            explanation,
        ),
    )
    return question_id
