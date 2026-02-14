from __future__ import annotations

from datetime import datetime

import pytest

from app.config import Settings
from app.models import ApprovalDecision, ApprovalRequest
from app.service import SentinelService


class FakeClickHouse:
    def __init__(self) -> None:
        self.insert_calls: list[tuple[str, list[list], list[str]]] = []

    def query_dicts(self, sql: str, parameters: dict | None = None) -> list[dict]:
        params = parameters or {}

        if "FROM cases" in sql:
            old = {
                "case_id": "CASE-1",
                "run_id": "run-old",
                "case_date": "2026-01-10",
                "country": "Kenya",
                "city": "Nairobi",
                "lat": -1.28,
                "lon": 36.81,
                "pathogen_label": "X",
                "normalized_json": "{}",
                "ground_truth_json": "{}",
                "created_at": datetime(2026, 1, 10, 10, 0, 0),
            }
            new = {
                **old,
                "run_id": "run-new",
                "created_at": datetime(2026, 1, 10, 11, 0, 0),
            }
            if "AND run_id" in sql:
                return [old] if params.get("run_id") == "run-old" else [new]
            return [new, old]

        if "FROM decisions" in sql:
            run_id = params.get("run_id", "run-new")
            return [
                {
                    "run_id": run_id,
                    "case_id": "CASE-1",
                    "fused_score": 8.0,
                    "severity": 8.0,
                    "confidence": 72.0,
                    "eligible_for_review": 1,
                    "rationale": "test rationale",
                    "contributions_json": "{\"genomics\": 8.1, \"epi\": 7.8, \"geo\": 7.2}",
                    "threshold": 0.7,
                    "created_at": datetime(2026, 1, 10, 10, 10, 0),
                }
            ]

        if "FROM agent_outputs" in sql:
            run_id = params.get("run_id", "run-new")
            return [
                {
                    "run_id": run_id,
                    "case_id": "CASE-1",
                    "agent_name": "meta",
                    "output_json": "{\"severity\": 8.0}",
                    "score": 8.0,
                    "confidence": 0.72,
                    "created_at": datetime(2026, 1, 10, 10, 11, 0),
                }
            ]

        if "FROM approvals" in sql:
            run_id = params.get("run_id", "run-new")
            return [
                {
                    "run_id": run_id,
                    "case_id": "CASE-1",
                    "status": "pending",
                    "reviewer_name": None,
                    "notes": "auto",
                    "dispatch_json": "{\"dispatched\": false}",
                    "timestamp": datetime(2026, 1, 10, 10, 12, 0),
                }
            ]

        if "FROM audit_logs" in sql:
            run_id = params.get("run_id", "run-new")
            return [
                {
                    "run_id": run_id,
                    "case_id": "CASE-1",
                    "event_type": "rag_context_built",
                    "actor": "system",
                    "payload_json": "{\"query_case\": {\"case_id\": \"CASE-1\"}}",
                    "timestamp": datetime(2026, 1, 10, 10, 13, 0),
                }
            ]

        return []

    def insert(self, table: str, rows: list[list], column_names: list[str]) -> None:
        self.insert_calls.append((table, rows, column_names))


class DummyEmbedder:
    def embed_text(self, text: str) -> list[float]:
        return [0.0]


class DummyRetriever:
    def build_past_outbreak_index(self, cases: list[dict]) -> None:
        return


class DummyDispatchManager:
    async def dispatch_if_approved(self, **kwargs) -> dict:
        return {"dispatched": False}


@pytest.mark.asyncio
async def test_get_case_details_uses_requested_run_scope() -> None:
    service = SentinelService(
        settings=Settings(use_bedrock=False, use_bedrock_embeddings=False, use_rerank=False),
        clickhouse=FakeClickHouse(),
        embedder=DummyEmbedder(),
        retriever=DummyRetriever(),
        dispatch_manager=DummyDispatchManager(),
    )

    result = await service.get_case_details(case_id="CASE-1", run_id="run-old")

    assert result.case["run_id"] == "run-old"
    assert result.decision is not None
    assert result.decision["run_id"] == "run-old"
    assert all(row["run_id"] == "run-old" for row in result.agent_outputs)
    assert all(row["run_id"] == "run-old" for row in result.approvals)
    assert all(row["run_id"] == "run-old" for row in result.audit_trail)


@pytest.mark.asyncio
async def test_apply_approval_targets_requested_run() -> None:
    clickhouse = FakeClickHouse()
    service = SentinelService(
        settings=Settings(use_bedrock=False, use_bedrock_embeddings=False, use_rerank=False),
        clickhouse=clickhouse,
        embedder=DummyEmbedder(),
        retriever=DummyRetriever(),
        dispatch_manager=DummyDispatchManager(),
    )

    await service.apply_approval(
        case_id="CASE-1",
        approval=ApprovalRequest(decision=ApprovalDecision.reject, run_id="run-old", reviewer_name="Alice"),
    )

    approval_inserts = [call for call in clickhouse.insert_calls if call[0] == "approvals"]
    assert approval_inserts
    row = approval_inserts[-1][1][0]
    assert row[0] == "CASE-1"
    assert row[1] == "run-old"
