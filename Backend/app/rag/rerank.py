from __future__ import annotations

import json
import logging
from typing import Any

import boto3

from app.config import Settings


LOGGER = logging.getLogger(__name__)


class Reranker:
    """Cohere Rerank v3.5 via Amazon Bedrock, with local cosine-sort fallback."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = None
        if settings.use_rerank:
            self._client = boto3.client("bedrock-runtime", **settings.boto3_credentials())

    def rerank(
        self,
        query: str,
        items: list[dict[str, Any]],
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        """Rerank RAG results.  Each item must have 'payload' and 'similarity'."""
        if not items:
            return items

        k = top_k or len(items)

        if self._client is not None:
            try:
                return self._rerank_bedrock(query=query, items=items, top_k=k)
            except Exception:
                LOGGER.exception("Cohere rerank failed; falling back to local sort")

        return self._rerank_local(items, top_k=k)

    # ------------------------------------------------------------------
    # Bedrock Cohere Rerank
    # ------------------------------------------------------------------

    def _rerank_bedrock(
        self,
        query: str,
        items: list[dict[str, Any]],
        top_k: int,
    ) -> list[dict[str, Any]]:
        documents = [self._item_to_text(it) for it in items]

        body = json.dumps({
            "query": query,
            "documents": documents,
            "top_n": min(top_k, len(documents)),
            "api_version": 2,
        })

        response = self._client.invoke_model(
            modelId=self.settings.bedrock_rerank_model_id,
            contentType="application/json",
            accept="application/json",
            body=body,
        )
        result = json.loads(response["body"].read())

        ranked_results = result.get("results", [])
        reranked: list[dict[str, Any]] = []
        for entry in ranked_results:
            idx = entry["index"]
            relevance = float(entry.get("relevance_score", 0.0))
            item = {**items[idx], "rerank_score": relevance}
            reranked.append(item)

        return reranked

    # ------------------------------------------------------------------
    # Local fallback – cosine similarity sort
    # ------------------------------------------------------------------

    @staticmethod
    def _rerank_local(items: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        scored = sorted(
            items,
            key=lambda it: (float(it.get("similarity", 0.0)), len(str(it.get("payload", "")))),
            reverse=True,
        )
        return scored[:top_k]

    @staticmethod
    def _item_to_text(item: dict[str, Any]) -> str:
        payload = item.get("payload", {})
        if isinstance(payload, dict):
            return json.dumps(payload, default=str)
        return str(payload)


# ---------------------------------------------------------------------------
# Backwards-compatible functional interface
# ---------------------------------------------------------------------------

def rerank_context(items: list[dict[str, Any]], enabled: bool = False) -> list[dict[str, Any]]:
    """Legacy helper – local-only sort (no Bedrock).  Kept for callers not yet
    migrated to the Reranker class."""
    if not enabled or not items:
        return items
    return Reranker._rerank_local(items, top_k=len(items))
