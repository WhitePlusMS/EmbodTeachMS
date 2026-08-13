"""课件知识库文档、切块和 SQLite 检索基础能力。

本包只提供可被现有应用注入的独立领域服务；数据库结构统一由 ``Database.initialize`` 管理。
"""

from .chunking import ChunkingConfig, KnowledgeChunk, chunk_document
from .document_store import KnowledgeBaseDocumentStore
from .models import DocumentStatus, KnowledgeBaseDocument, SearchResult
from .publisher import KnowledgeBasePublisher
from .searcher import KnowledgeBaseSearcher

__all__ = [
    "ChunkingConfig",
    "DocumentStatus",
    "KnowledgeBaseChunk",
    "KnowledgeBaseDocument",
    "KnowledgeBaseDocumentStore",
    "KnowledgeBasePublisher",
    "KnowledgeBaseSearcher",
    "SearchResult",
    "chunk_document",
]
