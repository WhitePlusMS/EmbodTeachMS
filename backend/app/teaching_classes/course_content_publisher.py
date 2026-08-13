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
        1. 将全部备课分段发布为知识模块并保存重点快照
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

        # 保存发布时的重点快照，避免切换备课文档后学生端丢失重点
        highlights = self._state.load_highlights(connection, session_row["id"])

        # 获取题目
        questions = self._state.load_questions(connection, session_row["id"])

        # 发布全部备课分段，并为对应正文保存重点快照
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
        1. 将全部备课分段发布为知识模块并保存重点快照
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

        # 保存发布时的重点快照，避免切换备课文档后学生端丢失重点
        highlights = self._state.load_highlights(connection, session_row["id"])

        # 获取题目
        questions = self._state.load_questions(connection, session_row["id"])

        # 作业同样保留全部备课分段，并为对应正文保存重点快照
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

    def publish_single_question(
        self,
        connection: sqlite3.Connection,
        class_id: str,
        question: dict,
    ) -> str:
        """发布一条课堂练习，不改变备课会话的整体发布状态。"""
        return self._insert_question(
            connection,
            class_id,
            "课堂练习",
            question,
            self._now(),
        )

    def publish_single_question_homework(
        self,
        connection: sqlite3.Connection,
        class_id: str,
        question: dict,
        title: str,
        due_at: int,
        description: str,
    ) -> PublishedHomeworkResult:
        """将一条题目发布为独立作业。"""
        now = self._now()
        question_content_id = self._insert_question(
            connection,
            class_id,
            "作业题目",
            question,
            now,
        )
        content_ids = [question_content_id]
        homework_id = self._publish_homework_content(
            connection,
            class_id,
            title,
            due_at,
            description,
            now,
            content_ids,
        )
        connection.execute(
            """
            INSERT INTO homework_questions (homework_id, question_id, ordinal)
            VALUES (?, ?, 0)
            """,
            (homework_id, question_content_id),
        )
        return {"content_ids": content_ids, "homework_id": homework_id}

    def _publish_knowledge_modules(
        self,
        connection: sqlite3.Connection,
        paragraph_rows: list[sqlite3.Row],
        highlights: list[dict[str, object]],
        class_id: str,
        now: int,
        content_ids: list[str],
    ) -> list[str]:
        """为每个备课分段创建知识模块，教学重点只作为阅读时的高亮标记。"""
        knowledge_module_ids = []

        highlights_by_paragraph: dict[int, list[dict[str, object]]] = {}
        for highlight in highlights:
            paragraph_ordinal = highlight.get("paragraphOrdinal")
            if isinstance(paragraph_ordinal, int):
                highlights_by_paragraph.setdefault(paragraph_ordinal, []).append(highlight)

        # 所有解析分段都必须成为学生可见课件，不能再由是否标记重点决定。
        for paragraph in paragraph_rows:
            paragraph_ordinal = paragraph["ordinal"]
            # 正文直接使用原始分段，保证重点 offset 相对于课件正文仍然准确，
            # 学生端可以在对应文字上显示黄色 mark，而不会把重点内容重复拼到正文后面。
            content = paragraph["content"]
            content_utf16_length = len(content.encode("utf-16-le")) // 2

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

            # 将重点复制到正式课件维度，后续备课会话切换文档也不会影响学生阅读。
            highlight_rows: list[tuple[str, str, int, int, int, int]] = []
            for highlight in highlights_by_paragraph.get(paragraph_ordinal, []):
                start_offset = highlight.get("startOffset")
                end_offset = highlight.get("endOffset")
                created_at = highlight.get("createdAt")
                if not isinstance(start_offset, int) or not isinstance(end_offset, int):
                    continue
                if start_offset < 0 or end_offset <= start_offset or end_offset > content_utf16_length:
                    continue
                if not isinstance(created_at, int):
                    created_at = now
                highlight_rows.append(
                    (
                        str(uuid.uuid4()),
                        content_id,
                        paragraph_ordinal,
                        start_offset,
                        end_offset,
                        created_at,
                    )
                )
            if highlight_rows:
                connection.executemany(
                    """
                    INSERT INTO course_content_highlights
                    (id, content_id, paragraph_ordinal, start_offset, end_offset, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    highlight_rows,
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
