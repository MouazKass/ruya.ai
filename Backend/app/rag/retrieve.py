from __future__ import annotations

import json
import logging
from datetime import date, datetime
from typing import Any

from app.config import Settings
from app.rag.embed import EmbeddingService, case_to_embedding_text
from app.rag.index import InMemoryVectorIndex, cosine_similarity
from app.rag.rerank import Reranker
from app.storage.clickhouse import ClickHouseClient


LOGGER = logging.getLogger(__name__)


class Retriever:
    def __init__(self, settings: Settings, clickhouse: ClickHouseClient, embedder: EmbeddingService) -> None:
        self.settings = settings
        self.clickhouse = clickhouse
        self.embedder = embedder
        self.past_outbreak_index = InMemoryVectorIndex()
        self.reranker = Reranker(settings)

    def build_past_outbreak_index(self, cases: list[dict[str, Any]]) -> None:
        self.past_outbreak_index.clear()
        for case in cases:
            text = case_to_embedding_text(case)
            emb = self.embedder.embed_text(text)
            payload = {
                "case_id": case.get("case_id"),
                "country": case.get("country"),
                "city": case.get("city"),
                "date": case.get("date"),
                "summary": text,
            }
            self.past_outbreak_index.add(item_id=str(case.get("case_id")), payload=payload, embedding=emb)
        LOGGER.info("Built past-outbreak vector index with %s records", len(cases))

    def retrieve(
        self,
        case_id: str,
        normalized_case: dict[str, Any],
        query_embedding: list[float],
        top_k: int | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        k = top_k or self.settings.rag_top_k
        current_case_date = _coerce_date(normalized_case.get("date"))

        from_clickhouse = self._search_clickhouse_cases(
            case_id=case_id,
            query_embedding=query_embedding,
            current_case_date=current_case_date,
            k=k,
        )
        overscan = max(k * 10, k + 8)
        from_past_all = self.past_outbreak_index.search(query_embedding=query_embedding, k=overscan)
        from_past = _filter_past_outbreak_hits(
            case_id=case_id,
            current_case_date=current_case_date,
            hits=from_past_all,
            top_k=k,
        )
        from_strategy = self._search_strategy_memory(query_embedding=query_embedding, k=k)

        # Build a query string for Cohere rerank
        query_text = case_to_embedding_text(normalized_case)

        return {
            "clickhouse_records": _strip_heavy_fields(self.reranker.rerank(query_text, from_clickhouse, top_k=k)),
            "past_outbreak_cases": _strip_heavy_fields(self.reranker.rerank(query_text, from_past, top_k=k)),
            "strategy_memory": _strip_heavy_fields(self.reranker.rerank(query_text, from_strategy, top_k=k)),
            "query_case": {
                "case_id": case_id,
                "country": normalized_case.get("country"),
                "city": normalized_case.get("city"),
            },
        }

    def _search_clickhouse_cases(
        self,
        case_id: str,
        query_embedding: list[float],
        current_case_date: date | None,
        k: int,
    ) -> list[dict[str, Any]]:
        limit = int(self.settings.max_vector_scan)
        rows = self.clickhouse.query_dicts(
            f"""
            SELECT case_id, run_id, case_date, normalized_json, embedding, created_at
            FROM cases
            ORDER BY created_at DESC
            LIMIT {limit}
            """
        )

        scored: list[dict[str, Any]] = []
        for row in rows:
            if row.get("case_id") == case_id:
                continue
            if current_case_date is not None:
                row_case_date = _coerce_date(row.get("case_date"))
                if row_case_date is not None and row_case_date > current_case_date:
                    continue
            emb = [float(v) for v in row.get("embedding", [])]
            similarity = cosine_similarity(query_embedding, emb)
            normalized = _loads_json(row.get("normalized_json"))
            scored.append(
                {
                    "item_id": str(row.get("case_id")),
                    "similarity": similarity,
                    "payload": {
                        "run_id": row.get("run_id"),
                        "summary": {
                            "country": normalized.get("country"),
                            "city": normalized.get("city"),
                            "pathogen_label": normalized.get("pathogen_label"),
                            "date": normalized.get("date") or row.get("case_date"),
                        },
                    },
                }
            )

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:k]

    def _search_strategy_memory(self, query_embedding: list[float], k: int) -> list[dict[str, Any]]:
        limit = int(self.settings.max_vector_scan)
        rows = self.clickhouse.query_dicts(
            f"""
            SELECT run_id, case_id, strategy_notes, updated_prompts_json, weights_json, threshold, embedding, created_at
            FROM strategy_memory
            ORDER BY created_at DESC
            LIMIT {limit}
            """
        )

        scored: list[dict[str, Any]] = []
        for row in rows:
            emb = [float(v) for v in row.get("embedding", [])]
            similarity = cosine_similarity(query_embedding, emb)
            scored.append(
                {
                    "item_id": f"{row.get('run_id')}::{row.get('case_id')}",
                    "similarity": similarity,
                    "payload": {
                        "run_id": row.get("run_id"),
                        "case_id": row.get("case_id"),
                        "strategy_notes": row.get("strategy_notes"),
                        "updated_prompts": _loads_json(row.get("updated_prompts_json")),
                        "weights": _loads_json(row.get("weights_json")),
                        "threshold": row.get("threshold"),
                    },
                }
            )

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:k]


def _loads_json(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not value:
        return {}
    try:
        parsed = json.loads(value)
        if isinstance(parsed, dict):
            return parsed
        return {}
    except json.JSONDecodeError:
        return {}


def _strip_heavy_fields(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove embedding vectors and other bulky fields before sending to LLM prompt."""
    heavy_keys = {"embedding", "normalized_json", "ground_truth", "ground_truth_json"}
    cleaned: list[dict[str, Any]] = []
    for item in items:
        light = {k: v for k, v in item.items() if k not in heavy_keys}
        # Also strip embeddings nested in payload
        if isinstance(light.get("payload"), dict):
            light["payload"] = {k: v for k, v in light["payload"].items() if k not in heavy_keys}
        cleaned.append(light)
    return cleaned


def _filter_past_outbreak_hits(
    case_id: str,
    current_case_date: date | None,
    hits: list[dict[str, Any]],
    top_k: int,
) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    for hit in hits:
        payload = hit.get("payload", {})
        if str(payload.get("case_id")) == case_id:
            continue

        if current_case_date is not None:
            hit_date = _coerce_date(payload.get("date"))
            if hit_date is not None and hit_date > current_case_date:
                continue

        filtered.append(hit)
        if len(filtered) >= top_k:
            break
    return filtered


def _coerce_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        return None

    text = value.strip()
    if not text:
        return None
    if "T" in text:
        text = text.split("T", 1)[0]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None
