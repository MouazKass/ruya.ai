from __future__ import annotations

from app.config import Settings
from app.rag.embed import EmbeddingService, case_to_embedding_text
from app.rag.retrieve import Retriever


class EmptyClickHouse:
    def query_dicts(self, sql: str, parameters: dict | None = None) -> list[dict]:
        return []


def _case(case_id: str, case_date: str) -> dict:
    return {
        "case_id": case_id,
        "country": "Kenya",
        "city": "Nairobi",
        "date": case_date,
        "pathogen_label": "Influenza-like Variant",
        "genomic": {
            "mutation_novelty": 0.4,
            "lineage_deviation": 0.5,
            "recombination_flag": False,
            "notes": "Synthetic note",
        },
        "epi_osint": {
            "news_snippets": ["signal one", "signal two"],
            "source_types": ["promed", "who_bulletin"],
            "anomaly_score": 0.55,
            "reliability_hint": 0.7,
        },
        "geo": {
            "travel_hub_score": 0.6,
            "population_density_score": 0.75,
            "border_connectivity": 0.4,
        },
        "ground_truth": {
            "true_outbreak": True,
            "true_severity": 8.0,
            "official_alert_date": "2026-01-22",
        },
    }


def test_past_outbreak_index_payload_excludes_ground_truth() -> None:
    settings = Settings(use_rerank=False, use_bedrock_embeddings=False)
    embedder = EmbeddingService(settings)
    retriever = Retriever(settings=settings, clickhouse=EmptyClickHouse(), embedder=embedder)

    retriever.build_past_outbreak_index([_case("CASE-OLD", "2026-01-03")])
    assert retriever.past_outbreak_index._items
    assert "ground_truth" not in retriever.past_outbreak_index._items[0].payload


def test_retriever_excludes_self_and_future_cases_from_past_outbreak_context() -> None:
    settings = Settings(use_rerank=False, use_bedrock_embeddings=False)
    embedder = EmbeddingService(settings)
    retriever = Retriever(settings=settings, clickhouse=EmptyClickHouse(), embedder=embedder)

    old_case = _case("CASE-OLD", "2026-01-03")
    current_case = _case("CASE-NOW", "2026-01-10")
    future_case = _case("CASE-FUTURE", "2026-02-01")
    retriever.build_past_outbreak_index([old_case, current_case, future_case])

    query_embedding = embedder.embed_text(case_to_embedding_text(current_case))
    rag_context = retriever.retrieve(
        case_id=current_case["case_id"],
        normalized_case=current_case,
        query_embedding=query_embedding,
        top_k=5,
    )
    item_ids = [str(item.get("item_id")) for item in rag_context["past_outbreak_cases"]]

    assert "CASE-NOW" not in item_ids
    assert "CASE-FUTURE" not in item_ids
    assert "CASE-OLD" in item_ids
