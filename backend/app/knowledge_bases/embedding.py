"""千问 Embedding HTTP 适配器。

Embedding 是可选的语义索引增强能力。未配置服务时，知识库仍通过 FTS5 提供关键词检索；
调用失败时只标记向量索引失败，不伪造零向量，也不影响已经完成的文本解析结果。
"""

from __future__ import annotations

import json
import os
from urllib import request as url_request


class EmbeddingError(RuntimeError):
    """Embedding 服务不可用或返回了无法识别的结果。"""


class QwenEmbeddingClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("QWEN_API_KEY", "").strip()
        self.base_url = os.getenv(
            "QWEN_API_URL", "https://dashscope.aliyuncs.com/api/v1"
        ).rstrip("/")
        self.model = os.getenv("EMBEDDING_MODEL", "").strip()
        self.timeout_seconds = 60

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.model)

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not self.configured:
            raise EmbeddingError("EMBEDDING_NOT_CONFIGURED")
        if not texts:
            return []
        if any(len(text) > 6000 for text in texts):
            raise EmbeddingError("EMBEDDING_TEXT_TOO_LONG")
        payload = json.dumps(
            {"model": self.model, "input": {"texts": texts}},
            ensure_ascii=False,
        ).encode("utf-8")
        http_request = url_request.Request(
            f"{self.base_url}/services/embeddings/text-embedding/text-embedding",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with url_request.urlopen(http_request, timeout=self.timeout_seconds) as response:
                response_body = json.loads(response.read().decode("utf-8"))
        except Exception as error:
            raise EmbeddingError("EMBEDDING_REQUEST_FAILED") from error

        vectors = self._extract_vectors(response_body)
        if len(vectors) != len(texts) or any(not vector for vector in vectors):
            raise EmbeddingError("EMBEDDING_RESPONSE_INVALID")
        dimensions = len(vectors[0])
        if any(len(vector) != dimensions for vector in vectors):
            raise EmbeddingError("EMBEDDING_DIMENSIONS_MISMATCH")
        return vectors

    @staticmethod
    def _extract_vectors(payload: object) -> list[list[float]]:
        if not isinstance(payload, dict):
            return []
        output = payload.get("output")
        candidates: object = output
        if isinstance(output, dict):
            candidates = output.get("embeddings") or output.get("results")
        if candidates is None:
            candidates = payload.get("data")
        if not isinstance(candidates, list):
            return []
        vectors: list[list[float]] = []
        for item in candidates:
            if isinstance(item, dict):
                item = item.get("embedding")
            if not isinstance(item, list):
                return []
            try:
                vectors.append([float(value) for value in item])
            except (TypeError, ValueError):
                return []
        return vectors
