import json
import sqlite3
from typing import TypedDict

from app.common.errors import BusinessError
from app.teaching_classes.question_review import StoredQuestion

class PublicationDraft(TypedDict):
    """发布草稿状态记录。课程内容 ID 从 course_contents 关系反查。"""

    published_at: int | None
    course_content_ids: list[str]


class PreparationSessionStateStore:
    """备课状态的关系化持久化 adapter。

    重点和题目不再整列覆写 preparation_sessions 中的 JSON；每次读写都以
    session_id 为边界查询对应关系表，并用 preparation_sessions.state_revision
    保留乐观并发保护；updated_at 只负责展示最后变更时间。
    """

    def load_highlights(
        self, connection: sqlite3.Connection, session_id: str
    ) -> list[dict[str, object]]:
        rows = connection.execute(
            """
            SELECT id, segment_ordinal, start_offset, end_offset, created_at
            FROM preparation_highlights
            WHERE session_id = ?
            ORDER BY segment_ordinal, start_offset, end_offset, id
            """,
            (session_id,),
        ).fetchall()
        return [
            {
                "id": row["id"],
                "paragraphOrdinal": row["segment_ordinal"],
                "startOffset": row["start_offset"],
                "endOffset": row["end_offset"],
                "createdAt": row["created_at"],
            }
            for row in rows
        ]

    def load_questions(
        self,
        connection: sqlite3.Connection,
        session_id: str,
    ) -> list[StoredQuestion]:
        """读取备课题目关系；数组字段仅作为题目值对象保留 JSON。"""
        rows = connection.execute(
            """
            SELECT id, source, review_status, question_type, stem, options_json,
                   correct_answers_json, knowledge_points_json,
                   highlight_source_ids_json, hint, explanation,
                   created_at, updated_at
            FROM preparation_questions
            WHERE session_id = ?
            ORDER BY created_at, id
            """,
            (session_id,),
        ).fetchall()
        return [
            StoredQuestion(
                id=row["id"],
                source=row["source"],
                review_status=row["review_status"],
                type=row["question_type"],
                stem=row["stem"],
                options=json.loads(row["options_json"] or "[]"),
                answers=json.loads(row["correct_answers_json"] or "[]"),
                knowledge_points=json.loads(row["knowledge_points_json"] or "[]"),
                highlight_source_ids=json.loads(row["highlight_source_ids_json"] or "[]"),
                hint=row["hint"],
                explanation=row["explanation"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def _begin_state_update(
        self,
        connection: sqlite3.Connection,
        session_id: str,
        expected_revision: int,
        now: int,
    ) -> None:
        updated = connection.execute(
            """
            UPDATE preparation_sessions
            SET updated_at = ?, state_revision = state_revision + 1
            WHERE id = ? AND state_revision = ?
            """,
            (now, session_id, expected_revision),
        )
        if updated.rowcount != 1:
            raise BusinessError(
                status_code=409,
                code="PREPARATION_SESSION_CONFLICT",
                message="备课会话已被其他操作修改，请刷新后重试",
            )

    def save_highlights(
        self,
        connection: sqlite3.Connection,
        session: sqlite3.Row,
        highlights: list[dict[str, object]],
        now: int,
    ) -> None:
        self._begin_state_update(connection, session["id"], session["state_revision"], now)
        connection.execute(
            "DELETE FROM preparation_highlights WHERE session_id = ?", (session["id"],)
        )
        connection.executemany(
            """
            INSERT INTO preparation_highlights
                (id, session_id, segment_ordinal, start_offset, end_offset, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    str(item["id"]),
                    session["id"],
                    int(item["paragraphOrdinal"]),
                    int(item["startOffset"]),
                    int(item["endOffset"]),
                    int(item["createdAt"]),
                )
                for item in highlights
            ],
        )

    def save_questions(
        self,
        connection: sqlite3.Connection,
        session: sqlite3.Row,
        questions: list[StoredQuestion],
        now: int,
    ) -> None:
        self._begin_state_update(connection, session["id"], session["state_revision"], now)
        connection.execute(
            "DELETE FROM preparation_questions WHERE session_id = ?", (session["id"],)
        )
        connection.executemany(
            """
            INSERT INTO preparation_questions
                (id, session_id, source, review_status, question_type, stem,
                 options_json, correct_answers_json, knowledge_points_json,
                 highlight_source_ids_json, hint, explanation, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    question["id"],
                    session["id"],
                    question["source"],
                    question["review_status"],
                    question["type"],
                    question["stem"],
                    json.dumps(question["options"], separators=(",", ":")),
                    json.dumps(question["answers"], separators=(",", ":")),
                    json.dumps(question["knowledge_points"], separators=(",", ":")),
                    json.dumps(question["highlight_source_ids"], separators=(",", ":")),
                    question["hint"],
                    question["explanation"],
                    question["created_at"],
                    now,
                )
                for question in questions
            ],
        )

    def load_publication_draft(
        self,
        connection: sqlite3.Connection,
        session_id: str,
    ) -> PublicationDraft:
        """读取关系化发布标记，并从课程内容关系反查已发布内容。"""
        draft = connection.execute(
            """
            SELECT published_at, published_content_ids_json
            FROM preparation_sessions
            WHERE id = ?
            """,
            (session_id,),
        ).fetchone()
        content_ids = connection.execute(
            "SELECT cpc.content_id FROM course_publication_contents cpc JOIN course_publications cp ON cp.id = cpc.publication_id WHERE cp.preparation_session_id = ? ORDER BY cpc.ordinal",
            (session_id,),
        ).fetchall()
        relation_content_ids = [row["content_id"] for row in content_ids]
        stored_content_ids = json.loads(
            draft["published_content_ids_json"] if draft else "[]"
        )
        return {
            "published_at": draft["published_at"] if draft else None,
            "course_content_ids": relation_content_ids or stored_content_ids,
        }

    def save_publication_draft(
        self,
        connection: sqlite3.Connection,
        session_id: str,
        draft: PublicationDraft,
        now: int,
        *,
        current_step: str | None = None,
    ) -> None:
        """按会话 upsert 发布草稿；内容 ID由发布产生的 course_contents 关系承载。"""
        assignments = [
            "published_at = ?",
            "published_content_ids_json = ?",
            "updated_at = ?",
        ]
        parameters: list[object] = [
            draft["published_at"],
            json.dumps(draft["course_content_ids"], separators=(",", ":")),
            now,
        ]
        if current_step is not None:
            assignments.insert(0, "current_step = ?")
            parameters.insert(0, current_step)
        parameters.append(session_id)
        connection.execute(
            f"UPDATE preparation_sessions SET {', '.join(assignments)} WHERE id = ?",
            parameters,
        )
