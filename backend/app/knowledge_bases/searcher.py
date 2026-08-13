"""知识库混合检索模块。

从 KnowledgeBaseService 提取的独立检索模块，负责 FTS5 关键词检索、
向量语义检索以及两者的混合评分。
"""
from __future__ import annotations

import json
import logging
import math
import re
import sqlite3
from collections.abc import Callable

from app.knowledge_bases.models import (
    KnowledgeBaseSearchResultView,
    KnowledgeBaseSearchView,
    KnowledgeBaseRetrievalTestRequest,
    KnowledgeBaseIndexStatusView,
)
from app.knowledge_bases.embedding import EmbeddingError, QwenEmbeddingClient


logger = logging.getLogger("course_agent.knowledge_bases.searcher")


class KnowledgeBaseSearcher:
    """知识库检索器：FTS5 关键词 + 向量混合检索。"""

    def __init__(self, database_connect: Callable[[], sqlite3.Connection]) -> None:
        self._connect = database_connect

    # ── 对外搜索入口 ──────────────────────────────────────────────

    def search_for_knowledge_base(
        self, knowledge_base_id: str, query: str, limit: int
    ) -> KnowledgeBaseSearchView:
        """按知识库主键过滤检索。"""
        return self._hybrid_search(knowledge_base_id, query, limit)

    def retrieval_test(
        self,
        knowledge_base_id: str,
        request: KnowledgeBaseRetrievalTestRequest,
    ) -> KnowledgeBaseSearchView:
        """召回测试参数只进入当前调用，不覆盖正式知识库设置。"""
        return self._hybrid_search(
            knowledge_base_id,
            request.query,
            request.top_k,
            mode=request.mode,
            min_score=request.min_score,
        )

    def search_for_knowledge_base_as_user(
        self, knowledge_base_id: str, query: str, limit: int
    ) -> KnowledgeBaseSearchView:
        return self._hybrid_search(knowledge_base_id, query, limit)

    # ── 混合检索引擎 ──────────────────────────────────────────────

    def _hybrid_search(
        self,
        knowledge_base_id: str,
        query: str,
        limit: int,
        *,
        mode: str = "hybrid",
        min_score: float = 0.0,
    ) -> KnowledgeBaseSearchView:
        """执行一次临时检索；未配置 Embedding 时明确降级而不是伪造向量。"""
        raw_terms = re.findall(r"[\w一-鿿]+", query)
        terms = list(raw_terms)
        for raw_term in raw_terms:
            if re.fullmatch(r"[一-鿿]+", raw_term) and len(raw_term) > 2:
                terms.extend(raw_term[index : index + 2] for index in range(len(raw_term) - 1))
        if not terms:
            return KnowledgeBaseSearchView(
                results=[], retrieval_mode="fts5", has_results=False,
                query=query, top_k=limit, min_score=min_score,
            )
        fts_query = " OR ".join(f'"{term.replace(chr(34), "")}"' for term in terms)

        with self._connect() as connection:
            lexical_rows = []
            lexical_scores: dict[str, float] = {}
            if mode in {"keyword", "hybrid"}:
                try:
                    lexical_rows = connection.execute(
                        """SELECT f.chunk_id, c.document_id, d.original_filename,
                                  c.document_version, c.content, c.title_path_json,
                                  c.page_start, c.page_end, c.source_position,
                                  bm25(knowledge_base_chunks_fts) AS rank
                           FROM knowledge_base_chunks_fts f
                           JOIN knowledge_base_chunks c ON c.id = f.chunk_id
                           JOIN knowledge_base_documents d ON d.id = c.document_id
                           WHERE f.knowledge_base_id = ? AND f.content MATCH ?
                             AND d.parse_status = 'completed'
                           ORDER BY rank LIMIT ?""",
                        (knowledge_base_id, fts_query, limit * 4),
                    ).fetchall()
                except sqlite3.OperationalError:
                    lexical_rows = []
            if not lexical_rows:
                # unicode61 对连续中文句子的分词依赖 SQLite 版本；无 FTS 候选时，
                # 只在同一知识库的已索引正文中做短语包含评分。
                fallback_rows = connection.execute(
                    """
                    SELECT c.id AS chunk_id, c.document_id, d.original_filename,
                           c.document_version, c.content, c.title_path_json,
                           c.page_start, c.page_end, c.source_position
                    FROM knowledge_base_chunks c
                    JOIN knowledge_base_documents d ON d.id = c.document_id
                    WHERE c.knowledge_base_id = ? AND c.index_status = 'ready'
                      AND d.parse_status = 'completed'
                    """,
                    (knowledge_base_id,),
                ).fetchall()
                lexical_rows = []
                for row in fallback_rows:
                    haystack = f"{row['content']} {' '.join(json.loads(row['title_path_json']))}"
                    matched = sum(1 for term in terms if term and term in haystack)
                    if matched:
                        lexical_rows.append(row)
                        lexical_scores[row["chunk_id"]] = min(1.0, matched / len(terms))

            vector_rows = []
            if mode in {"vector", "hybrid"}:
                vector_rows = connection.execute(
                    """SELECT c.id AS chunk_id, embedding.vector_json AS vector_json,
                              c.document_id, d.original_filename,
                              c.document_version, c.content, c.title_path_json,
                              c.page_start, c.page_end, c.source_position
                       FROM knowledge_base_chunks c
                       JOIN knowledge_base_documents d ON d.id = c.document_id
                       JOIN knowledge_base_chunk_embeddings embedding ON embedding.chunk_id = c.id
                       WHERE c.knowledge_base_id = ? AND embedding.status = 'ready'
                         AND d.parse_status = 'completed'""",
                    (knowledge_base_id,),
                ).fetchall()

        candidates: dict[str, dict[str, object]] = {}
        for row in lexical_rows:
            lexical_score = lexical_scores.get(row["chunk_id"])
            if lexical_score is None:
                lexical_score = 1.0 / (1.0 + abs(float(row["rank"] or 0.0)))
            candidates[row["chunk_id"]] = {"row": row, "lexical": lexical_score, "semantic": 0.0}
        semantic_used = False
        fallback_reason: str | None = None
        client = QwenEmbeddingClient()
        if mode in {"vector", "hybrid"} and client.configured and vector_rows:
            try:
                query_vector = client.embed([query])[0]
                for row in vector_rows:
                    try:
                        vector = [float(value) for value in json.loads(row["vector_json"])]
                        denominator = (
                            math.sqrt(sum(value * value for value in query_vector))
                            * math.sqrt(sum(value * value for value in vector))
                        )
                        similarity = (
                            sum(left * right for left, right in zip(query_vector, vector)) / denominator
                            if denominator
                            else 0.0
                        )
                    except (TypeError, ValueError, json.JSONDecodeError):
                        continue
                    semantic_used = True
                    item = candidates.setdefault(
                        row["chunk_id"], {"row": row, "lexical": 0.0, "semantic": 0.0}
                    )
                    item["semantic"] = max(0.0, similarity)
            except EmbeddingError:
                semantic_used = False
                fallback_reason = "EMBEDDING_REQUEST_FAILED"
        elif mode in {"vector", "hybrid"}:
            fallback_reason = (
                "EMBEDDING_NOT_CONFIGURED"
                if not client.configured
                else "EMBEDDING_INDEX_NOT_READY"
            )

        ranked = sorted(
            candidates.values(),
            key=lambda item: (
                0.5 * float(item["lexical"]) + 0.5 * float(item["semantic"])
                if semantic_used
                else float(item["lexical"])
            ),
            reverse=True,
        )
        results: list[KnowledgeBaseSearchResultView] = []
        for item in ranked:
            row = item["row"]
            score = (
                0.5 * float(item["lexical"]) + 0.5 * float(item["semantic"])
                if semantic_used
                else float(item["lexical"])
            )
            if score < min_score:
                continue
            results.append(
                KnowledgeBaseSearchResultView(
                    chunk_id=row["chunk_id"],
                    document_id=row["document_id"],
                    document_filename=row["original_filename"],
                    document_version=row["document_version"],
                    content=row["content"],
                    title_path=json.loads(row["title_path_json"]),
                    page_start=row["page_start"],
                    page_end=row["page_end"],
                    source_position=row["source_position"],
                    score=score,
                )
            )
            if len(results) >= limit:
                break
        return KnowledgeBaseSearchView(
            results=results,
            retrieval_mode="hybrid" if semantic_used else "fts5",
            has_results=bool(results),
            query=query,
            top_k=limit,
            min_score=min_score,
            fallback_reason=fallback_reason,
        )

    # ── 索引状态查询 ──────────────────────────────────────────────

    def get_index_status(
        self, knowledge_base_id: str
    ) -> KnowledgeBaseIndexStatusView:
        with self._connect() as connection:
            count, ready, strategy = connection.execute(
                """SELECT COUNT(*), COALESCE(SUM(index_status = 'ready'), 0),
                          MAX(chunk_strategy_version)
                   FROM knowledge_base_chunks WHERE knowledge_base_id = ?""",
                (knowledge_base_id,),
            ).fetchone()
            embedding_rows = connection.execute(
                """SELECT embedding.status AS status, COUNT(*) AS count
                   FROM knowledge_base_chunk_embeddings embedding
                   JOIN knowledge_base_chunks chunk ON chunk.id = embedding.chunk_id
                   WHERE chunk.knowledge_base_id = ?
                   GROUP BY embedding.status""",
                (knowledge_base_id,),
            ).fetchall()
        embedding_counts = {row["status"]: row["count"] for row in embedding_rows}
        if not embedding_counts:
            embedding_status = "unconfigured"
        elif embedding_counts.get("failed"):
            embedding_status = "failed"
        elif embedding_counts.get("ready", 0) == count:
            embedding_status = "ready"
        else:
            embedding_status = "pending"
        return KnowledgeBaseIndexStatusView(
            knowledge_base_id=knowledge_base_id,
            chunk_count=count,
            ready_chunk_count=ready,
            retrieval_mode="hybrid" if embedding_status == "ready" else "fts5",
            embedding_status=embedding_status,
            chunk_strategy_version=strategy,
        )

    # ── 向量化 ────────────────────────────────────────────────────

    def vectorize_knowledge_base(
        self, knowledge_base_id: str
    ) -> str:
        """批量生成向量；未配置向量服务时保留 FTS5 检索基线。"""
        client = QwenEmbeddingClient()
        with self._connect() as connection:
            chunks = connection.execute(
                """SELECT c.id, c.content FROM knowledge_base_chunks c
                   JOIN knowledge_base_documents d ON d.id = c.document_id
                   WHERE c.knowledge_base_id = ? AND d.parse_status = 'completed'
                   ORDER BY c.ordinal""",
                (knowledge_base_id,),
            ).fetchall()
        if not chunks:
            return "unconfigured" if not client.configured else "ready"
        if not client.configured:
            return "unconfigured"

        failed = False
        for start in range(0, len(chunks), 8):
            batch = chunks[start : start + 8]
            try:
                vectors = client.embed([row["content"] for row in batch])
            except EmbeddingError as error:
                failed = True
                error_code = str(error) or "EMBEDDING_REQUEST_FAILED"
                with self._connect() as connection:
                    for row in batch:
                        connection.execute(
                            """INSERT INTO knowledge_base_chunk_embeddings
                               (chunk_id, model_name, dimensions, vector_json, status,
                                error_code, updated_at)
                               VALUES (?, ?, 1, '[]', 'failed', ?, ?)
                               ON CONFLICT(chunk_id) DO UPDATE SET
                                   model_name = excluded.model_name,
                                   dimensions = excluded.dimensions,
                                   vector_json = excluded.vector_json,
                                   status = excluded.status,
                                   error_code = excluded.error_code,
                                   updated_at = excluded.updated_at""",
                            (row["id"], client.model, error_code, connection.execute("SELECT unixepoch()").fetchone()[0]),
                        )
                continue

            dimensions = len(vectors[0])
            with self._connect() as connection:
                now = connection.execute("SELECT unixepoch()").fetchone()[0]
                for row, vector in zip(batch, vectors):
                    connection.execute(
                        """INSERT INTO knowledge_base_chunk_embeddings
                           (chunk_id, model_name, dimensions, vector_json, status,
                            error_code, updated_at)
                           VALUES (?, ?, ?, ?, 'ready', NULL, ?)
                           ON CONFLICT(chunk_id) DO UPDATE SET
                               model_name = excluded.model_name,
                               dimensions = excluded.dimensions,
                               vector_json = excluded.vector_json,
                               status = excluded.status,
                               error_code = excluded.error_code,
                               updated_at = excluded.updated_at""",
                        (row["id"], client.model, dimensions, json.dumps(vector), now),
                    )
        return "failed" if failed else "ready"
