import logging
import sqlite3
from pathlib import Path


# DDL 注册表：各模块通过 register_ddl 注册自己的 CREATE TABLE 片段，
# Database.initialize 在启动时按顺序执行它们。这使 DDL 与模块内聚，
# 减少 database.py 单一文件的修改频率。
_DDL_REGISTRY: list[str] = []

logger = logging.getLogger("course_agent.database")


def register_ddl(ddl: str) -> None:
    """供各模块在 import 时注册 DDL 片段。"""
    _DDL_REGISTRY.append(ddl)


class ClosingConnection(sqlite3.Connection):
    """事务上下文结束时同时释放底层 SQLite 句柄。"""

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


class Database:
    """集中管理 SQLite 连接约束，业务代码不自行配置连接。"""

    # 当前项目明确采用破坏式重建，不再为旧实验数据保留迁移兼容层。
    _SCHEMA_VERSION = 4

    def __init__(self, path: Path) -> None:
        self._path = path

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path, factory=ClosingConnection)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        connection.execute("PRAGMA synchronous = NORMAL")
        return connection

    @property
    def path(self) -> Path:
        """数据库同级目录用于受控的应用私有存储。"""
        return self._path

    def initialize(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            reset = self._reset_schema_for_clean_rebuild(connection)
            if reset:
                connection.commit()
                connection.execute("VACUUM")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('learner', 'teacher')),
                    created_at INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    expires_at INTEGER NOT NULL,
                    revoked_at INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS teaching_classes (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    join_policy TEXT NOT NULL CHECK (join_policy IN ('free', 'approval', 'closed')),
                    owner_teacher_id TEXT NOT NULL,
                    background TEXT NOT NULL DEFAULT '',
                    introduction TEXT NOT NULL DEFAULT '',
                    objectives TEXT NOT NULL DEFAULT '',
                    features TEXT NOT NULL DEFAULT '',
                    overview_updated_at INTEGER,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    FOREIGN KEY (owner_teacher_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS class_memberships (
                    class_id TEXT NOT NULL,
                    learner_id TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    FOREIGN KEY (class_id) REFERENCES teaching_classes(id) ON DELETE CASCADE,
                    FOREIGN KEY (learner_id) REFERENCES users(id) ON DELETE CASCADE,
                    PRIMARY KEY (class_id, learner_id)
                );

                CREATE INDEX IF NOT EXISTS idx_sessions_user_id
                ON sessions(user_id);

                CREATE INDEX IF NOT EXISTS idx_sessions_expires_at
                ON sessions(expires_at);

                CREATE INDEX IF NOT EXISTS idx_teaching_classes_owner_teacher_id
                ON teaching_classes(owner_teacher_id, updated_at DESC, id DESC);

                CREATE INDEX IF NOT EXISTS idx_class_memberships_learner_id
                ON class_memberships(learner_id, class_id);

                CREATE TABLE IF NOT EXISTS class_join_requests (
                    id TEXT PRIMARY KEY,
                    class_id TEXT NOT NULL,
                    learner_id TEXT NOT NULL,
                    status TEXT NOT NULL CHECK (status IN ('pending', 'approved', 'rejected')),
                    created_at INTEGER NOT NULL,
                    resolved_at INTEGER,
                    resolved_by_teacher_id TEXT,
                    FOREIGN KEY (class_id) REFERENCES teaching_classes(id) ON DELETE CASCADE,
                    FOREIGN KEY (learner_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (resolved_by_teacher_id) REFERENCES users(id) ON DELETE CASCADE,
                    UNIQUE(class_id, learner_id)
                );

                CREATE INDEX IF NOT EXISTS idx_class_join_requests_class_status_created
                ON class_join_requests(class_id, status, created_at ASC, id ASC);

                CREATE INDEX IF NOT EXISTS idx_class_join_requests_learner_created
                ON class_join_requests(learner_id, created_at DESC);

                CREATE TABLE IF NOT EXISTS class_authorization_codes (
                    id TEXT PRIMARY KEY,
                    class_id TEXT NOT NULL,
                    code TEXT NOT NULL UNIQUE,
                    enabled BOOLEAN NOT NULL DEFAULT TRUE,
                    expires_at INTEGER,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    FOREIGN KEY (class_id) REFERENCES teaching_classes(id) ON DELETE CASCADE,
                    UNIQUE(class_id)  -- 每个班级最多一个授权码
                );

                -- 统一课程内容表
                CREATE TABLE IF NOT EXISTS course_contents (
                    id TEXT PRIMARY KEY,
                    class_id TEXT NOT NULL,
                    content_type TEXT NOT NULL CHECK (content_type IN ('knowledge_point', 'knowledge_module', 'teaching_resource', 'question', 'competency_objective', 'homework')),
                    publication_status TEXT NOT NULL CHECK (publication_status IN ('draft', 'published')),
                    title TEXT NOT NULL,
                    content TEXT,
                    -- 作业特有字段
                    due_at INTEGER,
                    description TEXT,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    FOREIGN KEY (class_id) REFERENCES teaching_classes(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_course_contents_class_status_created
                ON course_contents(class_id, publication_status, created_at ASC);

                -- 客观题结构化事实；展示文本与判分答案不再共用 content 字段。
                CREATE TABLE IF NOT EXISTS course_content_questions (
                    content_id TEXT PRIMARY KEY,
                    question_type TEXT NOT NULL CHECK (question_type IN ('single_choice', 'multiple_choice')),
                    stem TEXT NOT NULL,
                    options_json TEXT NOT NULL,
                    correct_answers_json TEXT NOT NULL,
                    knowledge_points_json TEXT NOT NULL DEFAULT '[]',
                    hint TEXT NOT NULL DEFAULT '',
                    explanation TEXT NOT NULL DEFAULT '',
                    FOREIGN KEY (content_id) REFERENCES course_contents(id) ON DELETE CASCADE
                );

                -- 备课会话表
                CREATE TABLE IF NOT EXISTS preparation_sessions (
                    id TEXT PRIMARY KEY,
                    class_id TEXT NOT NULL UNIQUE,
                    owner_teacher_id TEXT NOT NULL,
                    original_filename TEXT,
                    file_format TEXT CHECK (file_format IN ('pdf', 'docx', 'markdown')),
                    file_size_bytes INTEGER CHECK (file_size_bytes > 0 AND file_size_bytes <= 20971520),
                    upload_status TEXT NOT NULL CHECK (upload_status IN ('waiting', 'uploaded')),
                    parse_status TEXT NOT NULL CHECK (parse_status IN ('not_started', 'parsing', 'completed', 'timed_out', 'failed')),
                    current_step TEXT NOT NULL CHECK (current_step IN ('upload', 'parsing', 'highlighting', 'questioning', 'publishing')),
                    storage_key TEXT,
                    parse_error_code TEXT,
                    parse_started_at INTEGER,
                    parse_completed_at INTEGER,
                    parsed_content_reference TEXT,
                    knowledge_base_id TEXT,
                    published_at INTEGER,
                    published_content_ids_json TEXT NOT NULL DEFAULT '[]',
                    state_revision INTEGER NOT NULL DEFAULT 0 CHECK (state_revision >= 0),
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    FOREIGN KEY (class_id) REFERENCES teaching_classes(id) ON DELETE CASCADE,
                    FOREIGN KEY (owner_teacher_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_preparation_sessions_owner_teacher_id
                ON preparation_sessions(owner_teacher_id);

                CREATE TABLE IF NOT EXISTS preparation_session_documents (
                    session_id TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
                    document_version INTEGER NOT NULL CHECK (document_version > 0),
                    created_at INTEGER NOT NULL,
                    PRIMARY KEY (session_id, document_id),
                    UNIQUE (session_id, ordinal),
                    FOREIGN KEY (session_id) REFERENCES preparation_sessions(id) ON DELETE CASCADE,
                    FOREIGN KEY (document_id) REFERENCES knowledge_base_documents(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS preparation_session_segments (
                    session_id TEXT NOT NULL,
                    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
                    document_id TEXT,
                    chunk_id TEXT,
                    document_version INTEGER,
                    block_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    PRIMARY KEY (session_id, ordinal),
                    FOREIGN KEY (session_id) REFERENCES preparation_sessions(id) ON DELETE CASCADE,
                    FOREIGN KEY (document_id) REFERENCES knowledge_base_documents(id) ON DELETE SET NULL,
                    FOREIGN KEY (chunk_id) REFERENCES knowledge_base_chunks(id) ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS preparation_highlights (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    segment_ordinal INTEGER NOT NULL,
                    start_offset INTEGER NOT NULL CHECK (start_offset >= 0),
                    end_offset INTEGER NOT NULL CHECK (end_offset > start_offset),
                    created_at INTEGER NOT NULL,
                    UNIQUE (session_id, segment_ordinal, start_offset, end_offset),
                    FOREIGN KEY (session_id, segment_ordinal)
                        REFERENCES preparation_session_segments(session_id, ordinal)
                        ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS preparation_questions (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    review_status TEXT NOT NULL,
                    question_type TEXT NOT NULL,
                    stem TEXT NOT NULL,
                    options_json TEXT NOT NULL,
                    correct_answers_json TEXT NOT NULL,
                    knowledge_points_json TEXT NOT NULL DEFAULT '[]',
                    highlight_source_ids_json TEXT NOT NULL DEFAULT '[]',
                    hint TEXT NOT NULL DEFAULT '',
                    explanation TEXT NOT NULL DEFAULT '',
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES preparation_sessions(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_preparation_questions_session
                ON preparation_questions(session_id, updated_at);

                -- 逐题发布记录；同一道题可分别发布为课堂练习和作业。
                CREATE TABLE IF NOT EXISTS preparation_question_publications (
                    question_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    class_id TEXT NOT NULL,
                    publication_mode TEXT NOT NULL CHECK (publication_mode IN ('classroom', 'homework')),
                    content_id TEXT NOT NULL UNIQUE,
                    homework_id TEXT,
                    created_at INTEGER NOT NULL,
                    PRIMARY KEY (question_id, publication_mode),
                    FOREIGN KEY (question_id) REFERENCES preparation_questions(id) ON DELETE CASCADE,
                    FOREIGN KEY (session_id) REFERENCES preparation_sessions(id) ON DELETE CASCADE,
                    FOREIGN KEY (class_id) REFERENCES teaching_classes(id) ON DELETE CASCADE,
                    FOREIGN KEY (content_id) REFERENCES course_contents(id) ON DELETE CASCADE,
                    FOREIGN KEY (homework_id) REFERENCES course_contents(id) ON DELETE SET NULL
                );

                CREATE INDEX IF NOT EXISTS idx_preparation_question_publications_session
                ON preparation_question_publications(session_id, created_at);

                -- 可复用课件知识库及其教学班独立副本。
                CREATE TABLE IF NOT EXISTS knowledge_bases (
                    id TEXT PRIMARY KEY,
                    owner_teacher_id TEXT NOT NULL,
                    class_id TEXT,
                    source_knowledge_base_id TEXT,
                    kind TEXT NOT NULL CHECK (kind IN ('reusable', 'class_copy')),
                    name TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    segment_mode TEXT NOT NULL CHECK (segment_mode IN ('simple', 'advanced')) DEFAULT 'simple',
                    segment_max_characters INTEGER NOT NULL DEFAULT 2400 CHECK (segment_max_characters >= 1),
                    segment_overlap_characters INTEGER NOT NULL DEFAULT 240 CHECK (segment_overlap_characters >= 0),
                    segment_separators_json TEXT NOT NULL DEFAULT '["#","##","###","\\n\\n","\\n","。","；","，"]',
                    segment_cleaning_rules_json TEXT NOT NULL DEFAULT '[]',
                    segment_index_version INTEGER NOT NULL DEFAULT 1 CHECK (segment_index_version > 0),
                    segment_settings_updated_at INTEGER,
                    status TEXT NOT NULL CHECK (status IN ('draft', 'available', 'archived')),
                    source_version INTEGER NOT NULL DEFAULT 1 CHECK (source_version > 0),
                    archived_at INTEGER,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    FOREIGN KEY (owner_teacher_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (class_id) REFERENCES teaching_classes(id) ON DELETE CASCADE,
                    FOREIGN KEY (source_knowledge_base_id) REFERENCES knowledge_bases(id),
                    CHECK (
                        (kind = 'reusable' AND class_id IS NULL)
                        OR (kind = 'class_copy' AND class_id IS NOT NULL)
                    )
                );

                CREATE INDEX IF NOT EXISTS idx_knowledge_bases_owner_teacher_id
                ON knowledge_bases(owner_teacher_id, updated_at);

                CREATE INDEX IF NOT EXISTS idx_knowledge_bases_class_id
                ON knowledge_bases(class_id, updated_at);

                CREATE INDEX IF NOT EXISTS idx_knowledge_bases_source_id
                ON knowledge_bases(source_knowledge_base_id);

                CREATE UNIQUE INDEX IF NOT EXISTS uq_reusable_knowledge_base_name
                ON knowledge_bases(owner_teacher_id, name)
                WHERE kind = 'reusable';

                CREATE UNIQUE INDEX IF NOT EXISTS uq_class_knowledge_base_copy
                ON knowledge_bases(class_id)
                WHERE kind = 'class_copy';

                CREATE TABLE IF NOT EXISTS knowledge_base_documents (
                    id TEXT PRIMARY KEY,
                    knowledge_base_id TEXT NOT NULL,
                    source_document_id TEXT,
                    title TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    file_format TEXT NOT NULL CHECK (file_format IN ('pdf', 'docx', 'markdown')),
                    version INTEGER NOT NULL DEFAULT 1 CHECK (version > 0),
                    parse_status TEXT NOT NULL CHECK (parse_status IN ('not_started', 'parsing', 'completed', 'failed')),
                    parser_name TEXT,
                    parser_version TEXT,
                    content_hash TEXT,
                    error_code TEXT,
                    error_message TEXT,
                    storage_key TEXT,
                    storage_created_at INTEGER,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE,
                    FOREIGN KEY (source_document_id) REFERENCES knowledge_base_documents(id) ON DELETE SET NULL
                );

                CREATE INDEX IF NOT EXISTS idx_knowledge_base_documents_knowledge_base_id
                ON knowledge_base_documents(knowledge_base_id, updated_at DESC, id DESC);

                CREATE INDEX IF NOT EXISTS idx_knowledge_base_documents_parse_status
                ON knowledge_base_documents(parse_status);

                CREATE TABLE IF NOT EXISTS knowledge_base_document_contents (
                    document_id TEXT PRIMARY KEY,
                    markdown_content TEXT NOT NULL,
                    FOREIGN KEY (document_id) REFERENCES knowledge_base_documents(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS knowledge_base_blocks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
                    block_type TEXT NOT NULL,
                    title_path_json TEXT NOT NULL DEFAULT '[]',
                    content TEXT NOT NULL,
                    page_number INTEGER,
                    source_position TEXT,
                    line_start INTEGER,
                    line_end INTEGER,
                    UNIQUE(document_id, ordinal),
                    FOREIGN KEY (document_id) REFERENCES knowledge_base_documents(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS knowledge_base_chunks (
                    id TEXT PRIMARY KEY,
                    knowledge_base_id TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    document_version INTEGER NOT NULL DEFAULT 1,
                    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
                    content TEXT NOT NULL,
                    title_path_json TEXT NOT NULL DEFAULT '[]',
                    page_start INTEGER,
                    page_end INTEGER,
                    source_position TEXT,
                    chunk_strategy_version TEXT NOT NULL,
                    index_status TEXT NOT NULL CHECK (index_status IN ('pending', 'ready', 'failed')),
                    UNIQUE(document_id, ordinal),
                    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE,
                    FOREIGN KEY (document_id) REFERENCES knowledge_base_documents(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_knowledge_base_chunks_scope
                ON knowledge_base_chunks(knowledge_base_id, document_id, index_status, ordinal);

                -- 备课重点按知识库文档持久化；切换当前备课文档时不丢失已保存重点。
                CREATE TABLE IF NOT EXISTS preparation_document_highlights (
                    id TEXT PRIMARY KEY,
                    class_id TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    document_version INTEGER NOT NULL CHECK (document_version > 0),
                    chunk_id TEXT NOT NULL,
                    start_offset INTEGER NOT NULL CHECK (start_offset >= 0),
                    end_offset INTEGER NOT NULL CHECK (end_offset > start_offset),
                    created_at INTEGER NOT NULL,
                    UNIQUE (document_id, chunk_id, start_offset, end_offset),
                    FOREIGN KEY (class_id) REFERENCES teaching_classes(id) ON DELETE CASCADE,
                    FOREIGN KEY (document_id) REFERENCES knowledge_base_documents(id) ON DELETE CASCADE,
                    FOREIGN KEY (chunk_id) REFERENCES knowledge_base_chunks(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_preparation_document_highlights_document
                ON preparation_document_highlights(document_id, document_version, chunk_id);

                CREATE TABLE IF NOT EXISTS knowledge_base_chunk_embeddings (
                    chunk_id TEXT PRIMARY KEY,
                    model_name TEXT NOT NULL,
                    dimensions INTEGER NOT NULL CHECK (dimensions > 0),
                    vector_json TEXT NOT NULL,
                    status TEXT NOT NULL CHECK (status IN ('pending', 'ready', 'failed')),
                    error_code TEXT,
                    updated_at INTEGER NOT NULL,
                    FOREIGN KEY (chunk_id) REFERENCES knowledge_base_chunks(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_knowledge_base_chunk_embeddings_status
                ON knowledge_base_chunk_embeddings(status, updated_at);

                CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_base_chunks_fts USING fts5(
                    chunk_id UNINDEXED,
                    knowledge_base_id UNINDEXED,
                    content,
                    title_path,
                    source_position,
                    tokenize = 'unicode61'
                );

                CREATE TABLE IF NOT EXISTS course_publications (
                    id TEXT PRIMARY KEY,
                    knowledge_base_id TEXT NOT NULL,
                    class_id TEXT NOT NULL,
                    version INTEGER NOT NULL CHECK (version > 0),
                    preparation_session_id TEXT,
                    created_at INTEGER NOT NULL,
                    UNIQUE(knowledge_base_id, version),
                    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE,
                    FOREIGN KEY (class_id) REFERENCES teaching_classes(id) ON DELETE CASCADE,
                    FOREIGN KEY (preparation_session_id) REFERENCES preparation_sessions(id) ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS course_publication_contents (
                    publication_id TEXT NOT NULL,
                    content_id TEXT NOT NULL,
                    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
                    PRIMARY KEY (publication_id, content_id),
                    UNIQUE (publication_id, ordinal),
                    FOREIGN KEY (publication_id) REFERENCES course_publications(id) ON DELETE CASCADE,
                    FOREIGN KEY (content_id) REFERENCES course_contents(id) ON DELETE CASCADE
                );

                -- 正式课件重点快照；发布后不依赖备课会话的临时重点状态。
                CREATE TABLE IF NOT EXISTS course_content_highlights (
                    id TEXT PRIMARY KEY,
                    content_id TEXT NOT NULL,
                    paragraph_ordinal INTEGER NOT NULL CHECK (paragraph_ordinal >= 0),
                    start_offset INTEGER NOT NULL CHECK (start_offset >= 0),
                    end_offset INTEGER NOT NULL CHECK (end_offset > start_offset),
                    created_at INTEGER NOT NULL,
                    FOREIGN KEY (content_id) REFERENCES course_contents(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_course_content_highlights_content
                ON course_content_highlights(content_id, paragraph_ordinal, start_offset, end_offset);

                CREATE TABLE IF NOT EXISTS course_publication_documents (
                    publication_id TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    document_version INTEGER NOT NULL CHECK (document_version > 0),
                    PRIMARY KEY (publication_id, document_id),
                    FOREIGN KEY (publication_id) REFERENCES course_publications(id) ON DELETE CASCADE,
                    FOREIGN KEY (document_id) REFERENCES knowledge_base_documents(id) ON DELETE CASCADE
                );

                -- 课程内容完成记录表
                CREATE TABLE IF NOT EXISTS course_content_completions (
                    id TEXT PRIMARY KEY,
                    learner_id TEXT NOT NULL,
                    class_id TEXT NOT NULL,
                    content_id TEXT NOT NULL,
                    completed_at INTEGER NOT NULL,
                    created_at INTEGER NOT NULL,
                    FOREIGN KEY (learner_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (class_id) REFERENCES teaching_classes(id) ON DELETE CASCADE,
                    FOREIGN KEY (content_id) REFERENCES course_contents(id) ON DELETE CASCADE,
                    UNIQUE(learner_id, class_id, content_id)  -- 唯一约束保证幂等性
                );

                CREATE INDEX IF NOT EXISTS idx_course_content_completions_class_id
                ON course_content_completions(class_id, learner_id, content_id);

                CREATE INDEX IF NOT EXISTS idx_course_content_completions_content_id
                ON course_content_completions(content_id);

                CREATE INDEX IF NOT EXISTS idx_course_content_completions_completed_at
                ON course_content_completions(completed_at);

                -- 课堂练习作答记录表
                CREATE TABLE IF NOT EXISTS classroom_practice_attempts (
                    id TEXT PRIMARY KEY,
                    learner_id TEXT NOT NULL,
                    class_id TEXT NOT NULL,
                    content_id TEXT NOT NULL,
                    selected_answers TEXT NOT NULL, -- JSON 数组存储选中的答案索引
                    is_correct BOOLEAN NOT NULL,
                    attempted_at INTEGER NOT NULL,
                    created_at INTEGER NOT NULL,
                    FOREIGN KEY (learner_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (class_id) REFERENCES teaching_classes(id) ON DELETE CASCADE,
                    FOREIGN KEY (content_id) REFERENCES course_contents(id) ON DELETE CASCADE,
                    UNIQUE(learner_id, content_id)  -- 每个学习者对同一题目只能作答一次
                );

                CREATE INDEX IF NOT EXISTS idx_classroom_practice_attempts_learner_id
                ON classroom_practice_attempts(learner_id, class_id, attempted_at DESC);

                CREATE INDEX IF NOT EXISTS idx_classroom_practice_attempts_class_id
                ON classroom_practice_attempts(class_id);

                CREATE INDEX IF NOT EXISTS idx_classroom_practice_attempts_content_id
                ON classroom_practice_attempts(content_id);

                CREATE INDEX IF NOT EXISTS idx_classroom_practice_attempts_attempted_at
                ON classroom_practice_attempts(class_id, attempted_at DESC);

                -- 基准练习单次运行表；唯一键保证一个学习者对一个题目只形成一份证据
                CREATE TABLE IF NOT EXISTS baseline_practice_runs (
                    id TEXT PRIMARY KEY,
                    learner_id TEXT NOT NULL,
                    class_id TEXT NOT NULL,
                    content_id TEXT NOT NULL,
                    status TEXT NOT NULL CHECK (status IN ('initial', 'prompt_shown', 'completed', 'abandoned')),
                    first_attempt_answers TEXT NOT NULL DEFAULT '[]',
                    second_attempt_answers TEXT NOT NULL DEFAULT '[]',
                    final_answers TEXT NOT NULL DEFAULT '[]',
                    is_correct BOOLEAN,
                    correct_answers TEXT NOT NULL DEFAULT '[]',
                    explanation TEXT NOT NULL DEFAULT '',
                    question_type TEXT NOT NULL DEFAULT 'multiple_choice',
                    difficulty TEXT NOT NULL DEFAULT '',
                    knowledge_points TEXT NOT NULL DEFAULT '[]',
                    source TEXT NOT NULL DEFAULT '',
                    score INTEGER NOT NULL DEFAULT 0,
                    result_type TEXT CHECK (result_type IN ('first_correct','hint_correct','final_wrong','abandoned')),
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    FOREIGN KEY (learner_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (class_id) REFERENCES teaching_classes(id) ON DELETE CASCADE,
                    FOREIGN KEY (content_id) REFERENCES course_contents(id) ON DELETE CASCADE,
                    UNIQUE(learner_id, class_id, content_id)
                );

                CREATE INDEX IF NOT EXISTS idx_baseline_practice_runs_class_id
                ON baseline_practice_runs(class_id, learner_id, updated_at DESC);

                CREATE INDEX IF NOT EXISTS idx_baseline_practice_runs_content_id
                ON baseline_practice_runs(content_id);

                -- 作业提交记录表，支持草稿保存、正式提交、迟交标记和判分
                CREATE TABLE IF NOT EXISTS homework_submissions (
                    id TEXT PRIMARY KEY,
                    learner_id TEXT NOT NULL,
                    class_id TEXT NOT NULL,
                    homework_id TEXT NOT NULL,
                    -- 提交状态：draft=草稿，submitted=已提交
                    status TEXT NOT NULL CHECK (status IN ('draft', 'submitted')),
                    -- 答案内容：JSON格式存储题目ID和答案的映射
                    answers_json TEXT NOT NULL DEFAULT '{}',
                    -- 判分结果：JSON格式存储每题得分、正确答案、解析
                    grading_json TEXT NOT NULL DEFAULT '{}',
                    -- 总分和正确题目数
                    total_score INTEGER NOT NULL DEFAULT 0,
                    correct_count INTEGER NOT NULL DEFAULT 0,
                    -- 提交时间相关
                    draft_saved_at INTEGER,  -- 草稿保存时间
                    submitted_at INTEGER,    -- 正式提交时间
                    is_late_submission BOOLEAN NOT NULL DEFAULT FALSE,  -- 是否迟交
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    FOREIGN KEY (learner_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (class_id) REFERENCES teaching_classes(id) ON DELETE CASCADE,
                    FOREIGN KEY (homework_id) REFERENCES course_contents(id) ON DELETE CASCADE,
                    UNIQUE(learner_id, homework_id)  -- 每个学习者对同一作业只能有一条记录
                );

                CREATE INDEX IF NOT EXISTS idx_homework_submissions_learner_class
                ON homework_submissions(learner_id, class_id);

                CREATE INDEX IF NOT EXISTS idx_homework_submissions_class_id
                ON homework_submissions(class_id);

                CREATE INDEX IF NOT EXISTS idx_homework_submissions_homework_id
                ON homework_submissions(homework_id);

                -- 作业与客观题的显式关系，避免把班级内其他练习误计入作业。
                CREATE TABLE IF NOT EXISTS homework_questions (
                    homework_id TEXT NOT NULL,
                    question_id TEXT NOT NULL UNIQUE,
                    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
                    PRIMARY KEY (homework_id, question_id),
                    FOREIGN KEY (homework_id) REFERENCES course_contents(id) ON DELETE CASCADE,
                    FOREIGN KEY (question_id) REFERENCES course_contents(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_homework_questions_homework_id
                ON homework_questions(homework_id, ordinal);

                CREATE INDEX IF NOT EXISTS idx_homework_submissions_class_status_submitted
                ON homework_submissions(class_id, status, submitted_at DESC);

                CREATE TABLE IF NOT EXISTS webots_pairings (
                    id TEXT PRIMARY KEY,
                    class_id TEXT NOT NULL,
                    learner_id TEXT NOT NULL,
                    token_hash TEXT NOT NULL UNIQUE,
                    expires_at INTEGER NOT NULL,
                    used_at INTEGER,
                    created_at INTEGER NOT NULL,
                    FOREIGN KEY (class_id) REFERENCES teaching_classes(id) ON DELETE CASCADE,
                    FOREIGN KEY (learner_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_webots_pairings_class_learner_expires
                ON webots_pairings(class_id, learner_id, expires_at);

                CREATE TABLE IF NOT EXISTS webots_connectors (
                    connector_id TEXT NOT NULL,
                    class_id TEXT NOT NULL,
                    learner_id TEXT NOT NULL,
                    token_hash TEXT NOT NULL UNIQUE,
                    bound_at INTEGER NOT NULL,
                    environment_json TEXT NOT NULL DEFAULT '{}',
                    PRIMARY KEY (class_id, connector_id),
                    FOREIGN KEY (class_id) REFERENCES teaching_classes(id) ON DELETE CASCADE,
                    FOREIGN KEY (learner_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_webots_connectors_class_learner
                ON webots_connectors(class_id, learner_id);

                CREATE TABLE IF NOT EXISTS webots_runs (
                    id TEXT PRIMARY KEY,
                    class_id TEXT NOT NULL,
                    learner_id TEXT NOT NULL,
                    connector_id TEXT NOT NULL,
                    task_id TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL CHECK (status IN ('created','dispatched','running','completed','failed')),
                    epoch INTEGER NOT NULL DEFAULT 0,
                    result_json TEXT NOT NULL DEFAULT '{}',
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    FOREIGN KEY (class_id, connector_id) REFERENCES webots_connectors(class_id, connector_id),
                    FOREIGN KEY (learner_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_webots_runs_class_updated
                ON webots_runs(class_id, updated_at DESC, id DESC);

                CREATE INDEX IF NOT EXISTS idx_webots_runs_class_learner_updated
                ON webots_runs(class_id, learner_id, updated_at DESC, id DESC);

                CREATE TABLE IF NOT EXISTS webots_run_events (
                    run_id TEXT NOT NULL,
                    epoch INTEGER NOT NULL,
                    sequence INTEGER NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    PRIMARY KEY (run_id, epoch, sequence),
                    FOREIGN KEY (run_id) REFERENCES webots_runs(id) ON DELETE CASCADE
                );
                """
            )
            # 执行各模块通过 register_ddl 注册的 DDL 片段
            for ddl in _DDL_REGISTRY:
                connection.executescript(ddl)
            self._apply_schema_migrations(connection)

    def _reset_schema_for_clean_rebuild(self, connection: sqlite3.Connection) -> bool:
        """删除旧实验 schema，让本次启动只留下当前设计。

        这是一次性原型项目的显式破坏式升级。用户已确认数据库数据不重要，
        因此不保留旧表、旧列或隐式兼容视图，避免新旧模型长期并存。
        """
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        if version == self._SCHEMA_VERSION and self._table_exists(
            connection, "knowledge_base_document_contents"
        ) and self._table_exists(connection, "knowledge_base_chunk_embeddings"):
            return False

        table_names = [
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table', 'view')"
            ).fetchall()
            if row[0] not in {"sqlite_sequence"}
        ]
        connection.execute("PRAGMA foreign_keys = OFF")
        try:
            for table_name in table_names:
                connection.execute(f'DROP TABLE IF EXISTS "{table_name}"')
        finally:
            connection.execute("PRAGMA foreign_keys = ON")
        logger.warning(
            "database_schema_reset path=%s target_version=%s",
            self._path,
            self._SCHEMA_VERSION,
        )
        return True

    @staticmethod
    def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
        return connection.execute(
            "SELECT 1 FROM sqlite_master WHERE name = ? LIMIT 1", (table_name,)
        ).fetchone() is not None

    def _apply_schema_migrations(self, connection: sqlite3.Connection) -> None:
        """记录当前 schema 基线；旧数据不做增量兼容。"""
        connection.execute(f"PRAGMA user_version = {self._SCHEMA_VERSION}")
        connection.execute("PRAGMA optimize")
        logger.info(
            "database_schema_migrated path=%s version=%s journal_mode=WAL",
            self._path,
            self._SCHEMA_VERSION,
        )
