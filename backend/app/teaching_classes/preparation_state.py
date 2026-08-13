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

    def archive_session_highlights(
        self, connection: sqlite3.Connection, session_id: str
    ) -> None:
        """将当前会话中的知识库重点归档到文档维度。"""
        connection.execute(
            """
            INSERT INTO preparation_document_highlights
                (id, class_id, document_id, document_version, chunk_id,
                 start_offset, end_offset, created_at)
            SELECT h.id, s.class_id, s.document_id, s.document_version, s.chunk_id,
                   h.start_offset, h.end_offset, h.created_at
            FROM preparation_highlights h
            JOIN (
                SELECT p.session_id, p.ordinal, p.document_id, p.document_version,
                       p.chunk_id, ps.class_id
                FROM preparation_session_segments p
                JOIN preparation_sessions ps ON ps.id = p.session_id
                WHERE p.session_id = ?
            ) s ON s.session_id = h.session_id AND s.ordinal = h.segment_ordinal
            WHERE h.session_id = ? AND s.document_id IS NOT NULL AND s.chunk_id IS NOT NULL
            ON CONFLICT(document_id, chunk_id, start_offset, end_offset) DO UPDATE SET
                id = excluded.id,
                class_id = excluded.class_id,
                document_version = excluded.document_version,
                created_at = excluded.created_at
            """,
            (session_id, session_id),
        )
        self._sync_published_highlights(
            connection,
            session_id,
            self.load_highlights(connection, session_id),
        )

    @staticmethod
    def _sync_published_highlights(
        connection: sqlite3.Connection,
        session_id: str,
        highlights: list[dict[str, object]],
    ) -> None:
        """将当前备课重点同步到已发布课件对应的段落。"""
        published_modules = connection.execute(
            """
            SELECT cpc.content_id, cpc.ordinal
            FROM course_publications cp
            JOIN course_publication_contents cpc ON cpc.publication_id = cp.id
            JOIN course_contents cc ON cc.id = cpc.content_id
            WHERE cp.preparation_session_id = ?
              AND cc.content_type = 'knowledge_module'
            ORDER BY cpc.ordinal
            """,
            (session_id,),
        ).fetchall()
        if not published_modules:
            return

        content_by_paragraph = {
            int(row["ordinal"]): row["content_id"] for row in published_modules
        }
        content_ids = list(content_by_paragraph.values())
        placeholders = ",".join("?" for _ in content_ids)
        connection.execute(
            f"DELETE FROM course_content_highlights WHERE content_id IN ({placeholders})",
            content_ids,
        )

        snapshot_rows: list[tuple[str, str, int, int, int, int]] = []
        for highlight in highlights:
            paragraph_ordinal = highlight.get("paragraphOrdinal")
            start_offset = highlight.get("startOffset")
            end_offset = highlight.get("endOffset")
            created_at = highlight.get("createdAt")
            if not isinstance(paragraph_ordinal, int):
                continue
            content_id = content_by_paragraph.get(paragraph_ordinal)
            if content_id is None:
                continue
            if not isinstance(start_offset, int) or not isinstance(end_offset, int):
                continue
            if not isinstance(created_at, int):
                continue
            snapshot_rows.append(
                (
                    f"{content_id}:{highlight['id']}",
                    content_id,
                    paragraph_ordinal,
                    start_offset,
                    end_offset,
                    created_at,
                )
            )
        if snapshot_rows:
            connection.executemany(
                """
                INSERT INTO course_content_highlights
                (id, content_id, paragraph_ordinal, start_offset, end_offset, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                snapshot_rows,
            )

    def restore_document_highlights(
        self, connection: sqlite3.Connection, session_id: str
    ) -> None:
        """按当前会话段落恢复已保存的知识库重点。"""
        connection.execute(
            """
            INSERT INTO preparation_highlights
                (id, session_id, segment_ordinal, start_offset, end_offset, created_at)
            SELECT h.id, ?, s.ordinal, h.start_offset, h.end_offset, h.created_at
            FROM preparation_session_segments s
            JOIN preparation_document_highlights h
              ON h.document_id = s.document_id
             AND h.chunk_id = s.chunk_id
             AND h.document_version = s.document_version
            WHERE s.session_id = ?
            ON CONFLICT(id) DO UPDATE SET
                session_id = excluded.session_id,
                segment_ordinal = excluded.segment_ordinal,
                start_offset = excluded.start_offset,
                end_offset = excluded.end_offset,
                created_at = excluded.created_at
            """,
            (session_id, session_id),
        )

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
        previous_ids = {
            str(row["id"])
            for row in connection.execute(
                "SELECT id FROM preparation_highlights WHERE session_id = ?",
                (session["id"],),
            ).fetchall()
        }
        current_ids = {str(item["id"]) for item in highlights}
        removed_ids = previous_ids.difference(current_ids)
        if removed_ids:
            placeholders = ",".join("?" for _ in removed_ids)
            connection.execute(
                f"DELETE FROM preparation_document_highlights WHERE id IN ({placeholders})",
                tuple(removed_ids),
            )
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
        self.archive_session_highlights(connection, session["id"])

    def save_questions(
        self,
        connection: sqlite3.Connection,
        session: sqlite3.Row,
        questions: list[StoredQuestion],
        now: int,
    ) -> None:
        self._begin_state_update(connection, session["id"], session["state_revision"], now)
        if questions:
            placeholders = ",".join("?" for _ in questions)
            connection.execute(
                f"DELETE FROM preparation_questions WHERE session_id = ? AND id NOT IN ({placeholders})",
                [session["id"], *(question["id"] for question in questions)],
            )
        else:
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
            ON CONFLICT(id) DO UPDATE SET
                session_id = excluded.session_id,
                source = excluded.source,
                review_status = excluded.review_status,
                question_type = excluded.question_type,
                stem = excluded.stem,
                options_json = excluded.options_json,
                correct_answers_json = excluded.correct_answers_json,
                knowledge_points_json = excluded.knowledge_points_json,
                highlight_source_ids_json = excluded.highlight_source_ids_json,
                hint = excluded.hint,
                explanation = excluded.explanation,
                updated_at = excluded.updated_at
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
