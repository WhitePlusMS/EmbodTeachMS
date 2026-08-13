"""数据库 schema lifecycle 的最小回归测试。"""

import sqlite3
from pathlib import Path

from app.database import Database


def test_database_is_rebuilt_to_clean_schema_and_initialization_is_idempotent(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "legacy.db"
    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE knowledge_base_documents (
                id TEXT PRIMARY KEY,
                knowledge_base_id TEXT NOT NULL,
                source_document_id TEXT,
                title TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                file_format TEXT NOT NULL,
                parse_status TEXT NOT NULL,
                markdown_content TEXT,
                parser_name TEXT,
                parser_version TEXT,
                content_hash TEXT,
                error_code TEXT,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            );
            CREATE TABLE knowledge_base_publications (
                id TEXT PRIMARY KEY,
                knowledge_base_id TEXT NOT NULL,
                class_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                content_ids_json TEXT NOT NULL,
                created_at INTEGER NOT NULL
            );
            CREATE TABLE preparation_sessions (
                id TEXT PRIMARY KEY,
                class_id TEXT NOT NULL,
                owner_teacher_id TEXT NOT NULL,
                upload_status TEXT NOT NULL,
                parse_status TEXT NOT NULL,
                current_step TEXT NOT NULL,
                highlights_json TEXT NOT NULL,
                candidate_questions_json TEXT NOT NULL,
                publication_draft_json TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            );
            CREATE TABLE preparation_session_paragraphs (
                session_id TEXT NOT NULL,
                ordinal INTEGER NOT NULL,
                block_type TEXT NOT NULL,
                content TEXT NOT NULL,
                PRIMARY KEY (session_id, ordinal)
            );
            """
        )

    database = Database(database_path)
    database.initialize()
    database.initialize()

    with database.connect() as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 4
        assert connection.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        }
        assert {
            "preparation_session_documents",
            "preparation_session_segments",
            "preparation_highlights",
            "preparation_questions",
            "course_publications",
            "course_publication_contents",
            "course_publication_documents",
            "knowledge_base_document_contents",
            "knowledge_base_chunk_embeddings",
        } <= tables
        assert {
            "schema_migrations",
            "course_overviews",
            "knowledge_base_settings",
            "knowledge_base_document_sources",
            "preparation_session_paragraphs",
            "knowledge_base_publications",
            "preparation_publication_drafts",
        }.isdisjoint(tables)

        preparation_columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(preparation_sessions)")
        }
        assert "published_at" in preparation_columns
        assert "published_content_ids_json" in preparation_columns
        assert "state_revision" in preparation_columns

        document_columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(knowledge_base_documents)")
        }
        assert "markdown_content" not in document_columns
        assert "storage_key" in document_columns

        chunk_columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(knowledge_base_chunks)")
        }
        assert "embedding_vector_json" not in chunk_columns

        index_names = {
            row[1]
            for row in connection.execute(
                "SELECT type, name FROM sqlite_master WHERE type = 'index'"
            )
        }
        assert {
            "idx_sessions_expires_at",
            "idx_class_join_requests_class_status_created",
            "idx_course_contents_class_status_created",
            "idx_homework_submissions_class_status_submitted",
            "idx_webots_runs_class_updated",
        } <= index_names
