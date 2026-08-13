import json
import logging
import sqlite3
import uuid
from typing import TypedDict

from app.common.errors import BusinessError
from app.teaching_classes.models import ContentType
from app.teaching_classes.preparation_state import PreparationSessionStateStore

logger = logging.getLogger("course_agent.course_content_publisher")


class PublishedHomeworkResult(TypedDict):
    """作业发布事务需要继续使用的确定性结果。"""

    content_ids: list[str]
    homework_id: str


class CourseContentPublisher:
    """课程内容发布器，负责转换备课会话内容为统一课程内容"""

    def __init__(self, now_provider) -> None:
        self._now = now_provider
        self._state = PreparationSessionStateStore()

    def publish_course_content(
        self, connection: sqlite3.Connection, session_row: sqlite3.Row, class_id: str
    ) -> list[str]:
        """
        发布课程内容：
        1. 转换教学重点为知识模块
        2. 转换已确认题目为课堂练习
        3. 批量插入已发布状态的内容

        返回：创建的内容 ID 列表
        """
        now = self._now()
        content_ids = []

        # 获取备课会话段落
        paragraph_rows = connection.execute(
            """
            SELECT ordinal, block_type, content
            FROM preparation_session_segments
            WHERE session_id = ?
            ORDER BY ordinal
            """,
            (session_row["id"],),
        ).fetchall()

        # 获取教学重点
        highlights = self._state.load_highlights(connection, session_row["id"])

        # 获取题目
        questions = self._state.load_questions(connection, session_row["id"])

        # 转换教学重点为知识模块
        knowledge_module_ids = self._publish_knowledge_modules(
            connection, paragraph_rows, highlights, class_id, now, content_ids
        )

        # 转换已确认题目为课堂练习
        question_ids = self._publish_questions(
            connection, questions, class_id, now, content_ids
        )

        logger.info(
            "course_content_published session_id=%s class_id=%s "
            "knowledge_modules=%d questions=%d",
            session_row["id"],
            class_id,
            len(knowledge_module_ids),
            len(question_ids),
        )

        return content_ids

    def publish_homework(
        self,
        connection: sqlite3.Connection,
        session_row: sqlite3.Row,
        class_id: str,
        title: str,
        due_at: int,
        description: str
    ) -> PublishedHomeworkResult:
        """
        发布作业：
        1. 转换教学重点为知识模块
        2. 转换已确认题目为作业题目
        3. 创建作业内容记录

        返回：创建的全部内容 ID 与本次作业 ID
        """
        now = self._now()
        content_ids = []

        # 获取备课会话段落
        paragraph_rows = connection.execute(
            """
            SELECT ordinal, block_type, content
            FROM preparation_session_segments
            WHERE session_id = ?
            ORDER BY ordinal
            """,
            (session_row["id"],),
        ).fetchall()

        # 获取教学重点
        highlights = self._state.load_highlights(connection, session_row["id"])

        # 获取题目
        questions = self._state.load_questions(connection, session_row["id"])

        # 转换教学重点为知识模块
        knowledge_module_ids = self._publish_knowledge_modules(
            connection, paragraph_rows, highlights, class_id, now, content_ids
        )

        # 转换已确认题目为作业题目
        homework_question_ids = self._publish_homework_questions(
            connection, questions, class_id, now, content_ids
        )

        # 创建作业内容记录
        homework_id = self._publish_homework_content(
            connection, class_id, title, due_at, description, now, content_ids
        )
        connection.executemany(
            """
            INSERT INTO homework_questions (homework_id, question_id, ordinal)
            VALUES (?, ?, ?)
            """,
            [
                (homework_id, question_id, ordinal)
                for ordinal, question_id in enumerate(homework_question_ids)
            ],
        )

        logger.info(
            "homework_published session_id=%s class_id=%s "
            "knowledge_modules=%d homework_questions=%d homework_id=%s",
            session_row["id"],
            class_id,
            len(knowledge_module_ids),
            len(homework_question_ids),
            homework_id,
        )

        return {"content_ids": content_ids, "homework_id": homework_id}

    def _publish_knowledge_modules(
        self,
        connection: sqlite3.Connection,
        paragraph_rows: list[sqlite3.Row],
        highlights: list[dict],
        class_id: str,
        now: int,
        content_ids: list[str],
    ) -> list[str]:
        """转换教学重点为知识模块"""
        knowledge_module_ids = []

        # 按段落分组教学重点
        highlights_by_paragraph = {}
        for highlight in highlights:
            paragraph_ordinal = highlight["paragraphOrdinal"]
            if paragraph_ordinal not in highlights_by_paragraph:
                highlights_by_paragraph[paragraph_ordinal] = []
            highlights_by_paragraph[paragraph_ordinal].append(highlight)

        # 为每个有重点的段落创建知识模块
        for paragraph in paragraph_rows:
            paragraph_ordinal = paragraph["ordinal"]
            paragraph_highlights = highlights_by_paragraph.get(paragraph_ordinal, [])

            if not paragraph_highlights:
                continue

            # 创建知识模块内容
            content_parts = [f"段落 {paragraph_ordinal}: {paragraph['content']}"]

            # 添加重点内容
            for i, highlight in enumerate(paragraph_highlights, 1):
                start = highlight["startOffset"]
                end = highlight["endOffset"]
                highlighted_text = paragraph['content'][start:end]
                content_parts.append(f"教学重点 {i}: {highlighted_text}")

            content = "\n\n".join(content_parts)

            # 插入知识模块
            content_id = str(uuid.uuid4())
            connection.execute(
                """
                INSERT INTO course_contents
                (id, class_id, content_type, publication_status, title, content, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    content_id,
                    class_id,
                    ContentType.KNOWLEDGE_MODULE.value,
                    "published",
                    f"知识模块 - 段落 {paragraph_ordinal}",
                    content,
                    now,
                    now,
                ),
            )

            knowledge_module_ids.append(content_id)
            content_ids.append(content_id)

        return knowledge_module_ids

    def _publish_questions(
        self,
        connection: sqlite3.Connection,
        questions: list[dict],
        class_id: str,
        now: int,
        content_ids: list[str],
    ) -> list[str]:
        """转换已确认题目为课堂练习"""
        question_ids = []

        # 只发布已确认的题目
        confirmed_questions = [
            q for q in questions if q.get("review_status") == "confirmed"
        ]

        for i, question in enumerate(confirmed_questions, 1):
            content_id = self._insert_question(
                connection,
                class_id,
                f"课堂练习 {i}",
                question,
                now,
            )

            question_ids.append(content_id)
            content_ids.append(content_id)

        return question_ids

    def _publish_homework_questions(
        self,
        connection: sqlite3.Connection,
        questions: list[dict],
        class_id: str,
        now: int,
        content_ids: list[str],
    ) -> list[str]:
        """转换已确认题目为作业题目"""
        question_ids = []

        # 只发布已确认的题目
        confirmed_questions = [
            q for q in questions if q.get("review_status") == "confirmed"
        ]

        for i, question in enumerate(confirmed_questions, 1):
            content_id = self._insert_question(
                connection,
                class_id,
                f"作业题目 {i}",
                question,
                now,
            )

            question_ids.append(content_id)
            content_ids.append(content_id)

        return question_ids

    @staticmethod
    def _insert_question(
        connection: sqlite3.Connection,
        class_id: str,
        title: str,
        question: dict,
        now: int,
    ) -> str:
        """一次写入题目公开内容与私有判分事实。"""
        content_id = str(uuid.uuid4())
        stem = question["stem"]
        connection.execute(
            """
            INSERT INTO course_contents
            (id, class_id, content_type, publication_status, title, content, created_at, updated_at)
            VALUES (?, ?, ?, 'published', ?, ?, ?, ?)
            """,
            (
                content_id,
                class_id,
                ContentType.QUESTION.value,
                title,
                stem,
                now,
                now,
            ),
        )
        connection.execute(
            """
            INSERT INTO course_content_questions (
                content_id, question_type, stem, options_json,
                correct_answers_json, knowledge_points_json, hint, explanation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                content_id,
                question.get("type", "multiple_choice"),
                stem,
                json.dumps(question["options"], ensure_ascii=False, separators=(",", ":")),
                json.dumps(sorted(question["answers"]), separators=(",", ":")),
                json.dumps(question.get("knowledge_points", []), ensure_ascii=False, separators=(",", ":")),
                question.get("hint", ""),
                question.get("explanation", ""),
            ),
        )
        return content_id

    def _publish_homework_content(
        self,
        connection: sqlite3.Connection,
        class_id: str,
        title: str,
        due_at: int,
        description: str,
        now: int,
        content_ids: list[str],
    ) -> str:
        """创建作业内容记录"""
        homework_id = str(uuid.uuid4())

        # 构建作业内容
        content_parts = [f"作业标题: {title}"]
        if description:
            content_parts.append(f"作业描述: {description}")
        content_parts.append(f"截止时间: {due_at}")

        content = "\n\n".join(content_parts)

        connection.execute(
            """
            INSERT INTO course_contents
            (id, class_id, content_type, publication_status, title, content, due_at, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                homework_id,
                class_id,
                ContentType.HOMEWORK.value,
                "published",
                title,
                content,
                due_at,
                description,
                now,
                now,
            ),
        )

        content_ids.append(homework_id)
        return homework_id
