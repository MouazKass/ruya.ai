from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import HTTPException

from app.agents.epi_osint import EpiOsintAgent
from app.agents.genomics import GenomicsAgent
from app.agents.ingest import IngestAgent
from app.agents.meta import MetaAgent
from app.config import Settings
from app.dispatch.base import DispatchManager
from app.improve.evaluate import compute_run_metrics
from app.improve.update import (
    build_strategy_update,
    default_fusion_state,
    fusion_state_from_memory_row,
    update_fusion_state,
)
from app.models import (
    ApprovalDecision,
    ApprovalRequest,
    ApprovalResponse,
    ApprovalStatus,
    CaseDetailResponse,
    CaseMetricInput,
    CaseSummary,
    DashboardResponse,
    FusionState,
    RawCaseInput,
    RunStatusResponse,
    SuggestionExecuteRequest,
    SuggestionExecuteResponse,
)
from app.rag.embed import EmbeddingService, case_to_embedding_text
from app.rag.retrieve import Retriever
from app.storage.audit import log_audit_event
from app.storage.clickhouse import ClickHouseClient


LOGGER = logging.getLogger(__name__)


class SentinelService:
    def __init__(
        self,
        settings: Settings,
        clickhouse: ClickHouseClient,
        embedder: EmbeddingService,
        retriever: Retriever,
        dispatch_manager: DispatchManager,
    ) -> None:
        self.settings = settings
        self.clickhouse = clickhouse
        self.embedder = embedder
        self.retriever = retriever
        self.dispatch_manager = dispatch_manager

        self.ingest_agent = IngestAgent(settings)
        self.genomics_agent = GenomicsAgent(settings)
        self.epi_agent = EpiOsintAgent(settings)
        self.meta_agent = MetaAgent(settings)

        self._synthetic_cases: list[dict[str, Any]] = []
        self._run_tasks: dict[str, asyncio.Task[None]] = {}
        self._run_status: dict[str, RunStatusResponse] = {}

    async def initialize(self) -> None:
        self._synthetic_cases = self._load_synthetic_cases()
        self.retriever.build_past_outbreak_index(self._synthetic_cases)

    async def close(self) -> None:
        for task in self._run_tasks.values():
            if not task.done():
                task.cancel()
        self.clickhouse.close()

    async def start_run(self, num_cases: int) -> str:
        run_id = str(uuid4())
        selected = self._synthetic_cases[:num_cases]
        started_at = datetime.utcnow()

        status = RunStatusResponse(
            run_id=run_id,
            status="running",
            processed=0,
            total=len(selected),
            started_at=started_at,
            ended_at=None,
            error=None,
        )
        self._run_status[run_id] = status

        config = {
            "num_cases": len(selected),
            "guardrail_severity_threshold": self.settings.guardrail_severity_threshold,
            "guardrail_confidence_threshold_pct": self.settings.guardrail_confidence_threshold_pct,
            "rag_top_k": self.settings.rag_top_k,
            "dispatch_dry_run": self.settings.dispatch_dry_run,
        }
        self._insert_run_event(
            run_id=run_id,
            status="running",
            started_at=started_at,
            ended_at=None,
            processed=0,
            total=len(selected),
            error=None,
            config=config,
        )
        log_audit_event(
            clickhouse=self.clickhouse,
            run_id=run_id,
            case_id=None,
            event_type="run_started",
            actor="system",
            payload=config,
        )

        task = asyncio.create_task(self._execute_run(run_id=run_id, selected_cases=selected, started_at=started_at))
        self._run_tasks[run_id] = task
        return run_id

    async def get_run_status(self, run_id: str) -> RunStatusResponse:
        if run_id in self._run_status:
            return self._run_status[run_id]

        rows = self.clickhouse.query_dicts(
            """
            SELECT run_id, status, processed, total, started_at, ended_at, error
            FROM runs
            WHERE run_id = {run_id:String}
            ORDER BY event_time DESC
            LIMIT 1
            """,
            parameters={"run_id": run_id},
        )
        if not rows:
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

        row = rows[0]
        return RunStatusResponse(
            run_id=row["run_id"],
            status=row["status"],
            processed=int(row.get("processed", 0)),
            total=int(row.get("total", 0)),
            started_at=row["started_at"],
            ended_at=row.get("ended_at"),
            error=row.get("error"),
        )

    async def get_dashboard(self) -> DashboardResponse:
        recent_rows = self.clickhouse.query_dicts(
            """
            SELECT case_id, run_id, country, city, case_date, created_at
            FROM cases
            ORDER BY created_at DESC
            LIMIT 100
            """
        )
        decision_rows = self.clickhouse.query_dicts(
            """
            SELECT case_id, run_id, severity, confidence, eligible_for_review, fused_score, suggestion, created_at
            FROM decisions
            ORDER BY created_at DESC
            LIMIT 1000
            """
        )
        approval_rows = self.clickhouse.query_dicts(
            """
            SELECT case_id, run_id, status, timestamp, reviewer_name, notes
            FROM approvals
            ORDER BY timestamp DESC
            LIMIT 1000
            """
        )

        latest_decisions = _latest_by_case_run(decision_rows)
        latest_approvals = _latest_by_case_run(approval_rows)

        case_summaries: list[CaseSummary] = []
        for row in recent_rows[:20]:
            case_id = row["case_id"]
            run_id = str(row.get("run_id", ""))
            key = (case_id, run_id)
            decision = latest_decisions.get(key, {})
            approval = latest_approvals.get(key, {})

            status_value = approval.get("status") or (
                ApprovalStatus.pending.value if int(decision.get("eligible_for_review", 0)) == 1 else ApprovalStatus.not_required.value
            )

            case_summaries.append(
                CaseSummary(
                    case_id=case_id,
                    run_id=run_id,
                    country=row.get("country", ""),
                    city=row.get("city", ""),
                    date=row.get("case_date"),
                    status=status_value,
                    severity=round(float(decision.get("severity", 0.0)), 3),
                    confidence=round(float(decision.get("confidence", 0.0)), 3),
                    eligible_for_review=bool(int(decision.get("eligible_for_review", 0))),
                    suggestion=str(decision.get("suggestion", "")),
                )
            )

        metrics_rows = self.clickhouse.query_dicts(
            """
            SELECT run_id, lead_time_days, false_alarm_rate, severity_mae, brier_score, computed_at
            FROM metrics
            ORDER BY computed_at DESC
            LIMIT 1
            """
        )
        current_metrics = metrics_rows[0] if metrics_rows else {}

        pending_queue = [
            {
                "case_id": c.case_id,
                "run_id": c.run_id,
                "severity": c.severity,
                "confidence": c.confidence,
                "status": c.status,
                "suggestion": c.suggestion,
            }
            for c in case_summaries
            if c.status == ApprovalStatus.pending.value and c.eligible_for_review
        ]

        details_summary = [
            {
                "case_id": c.case_id,
                "run_id": c.run_id,
                "severity": c.severity,
                "confidence": c.confidence,
                "eligible_for_review": c.eligible_for_review,
                "status": c.status,
                "suggestion": c.suggestion,
            }
            for c in case_summaries
        ]

        return DashboardResponse(
            recent_cases=case_summaries,
            current_run_metrics=current_metrics,
            pending_approvals_queue=pending_queue,
            case_details_summary=details_summary,
        )

    async def get_case_details(self, case_id: str, run_id: str | None = None) -> CaseDetailResponse:
        if run_id:
            case_rows = self.clickhouse.query_dicts(
                """
                SELECT case_id, run_id, case_date, country, city, lat, lon, pathogen_label, normalized_json, ground_truth_json, created_at
                FROM cases
                WHERE case_id = {case_id:String} AND run_id = {run_id:String}
                ORDER BY created_at DESC
                LIMIT 1
                """,
                parameters={"case_id": case_id, "run_id": run_id},
            )
        else:
            case_rows = self.clickhouse.query_dicts(
                """
                SELECT case_id, run_id, case_date, country, city, lat, lon, pathogen_label, normalized_json, ground_truth_json, created_at
                FROM cases
                WHERE case_id = {case_id:String}
                ORDER BY created_at DESC
                LIMIT 1
                """,
                parameters={"case_id": case_id},
            )
        if not case_rows:
            if run_id:
                raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found in run '{run_id}'")
            raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")

        case_row = case_rows[0]
        selected_run_id = str(case_row.get("run_id", ""))

        decision_rows = self.clickhouse.query_dicts(
            """
            SELECT run_id, case_id, fused_score, severity, confidence, eligible_for_review, rationale, contributions_json, threshold, suggestion, created_at
            FROM decisions
            WHERE case_id = {case_id:String} AND run_id = {run_id:String}
            ORDER BY created_at DESC
            LIMIT 1
            """,
            parameters={"case_id": case_id, "run_id": selected_run_id},
        )
        decision = decision_rows[0] if decision_rows else None
        suggestion_text = str(decision.get("suggestion", "")) if decision else ""

        agent_rows = self.clickhouse.query_dicts(
            """
            SELECT run_id, case_id, agent_name, output_json, score, confidence, created_at
            FROM agent_outputs
            WHERE case_id = {case_id:String} AND run_id = {run_id:String}
            ORDER BY created_at ASC
            """,
            parameters={"case_id": case_id, "run_id": selected_run_id},
        )

        approval_rows = self.clickhouse.query_dicts(
            """
            SELECT run_id, case_id, status, reviewer_name, notes, dispatch_json, timestamp
            FROM approvals
            WHERE case_id = {case_id:String} AND run_id = {run_id:String}
            ORDER BY timestamp DESC
            """,
            parameters={"case_id": case_id, "run_id": selected_run_id},
        )

        audit_rows = self.clickhouse.query_dicts(
            """
            SELECT run_id, case_id, event_type, actor, payload_json, timestamp
            FROM audit_logs
            WHERE case_id = {case_id:String} AND run_id = {run_id:String}
            ORDER BY timestamp DESC
            LIMIT 200
            """,
            parameters={"case_id": case_id, "run_id": selected_run_id},
        )

        rag_context = {}
        for event in audit_rows:
            if event.get("event_type") == "rag_context_built":
                rag_context = _loads_json(event.get("payload_json"))
                break

        case_payload = {
            **case_row,
            "normalized": _loads_json(case_row.get("normalized_json")),
            "ground_truth": _loads_json(case_row.get("ground_truth_json")),
        }

        outputs_payload = [
            {
                **row,
                "output": _loads_json(row.get("output_json")),
            }
            for row in agent_rows
        ]

        if decision is not None:
            decision = {
                **decision,
                "contributions": _loads_json(decision.get("contributions_json")),
            }

        approvals = [
            {
                **row,
                "dispatch": _loads_json(row.get("dispatch_json")),
            }
            for row in approval_rows
        ]

        audits = [
            {
                **row,
                "payload": _loads_json(row.get("payload_json")),
            }
            for row in audit_rows
        ]

        return CaseDetailResponse(
            case=case_payload,
            rag_context_sources=rag_context,
            agent_outputs=outputs_payload,
            decision=decision,
            approvals=approvals,
            audit_trail=audits,
            suggestion=suggestion_text,
        )

    async def apply_approval(self, case_id: str, approval: ApprovalRequest) -> ApprovalResponse:
        if approval.run_id:
            decision_rows = self.clickhouse.query_dicts(
                """
                SELECT run_id, case_id, severity, confidence, eligible_for_review, rationale, created_at
                FROM decisions
                WHERE case_id = {case_id:String} AND run_id = {run_id:String}
                ORDER BY created_at DESC
                LIMIT 1
                """,
                parameters={"case_id": case_id, "run_id": approval.run_id},
            )
        else:
            decision_rows = self.clickhouse.query_dicts(
                """
                SELECT run_id, case_id, severity, confidence, eligible_for_review, rationale, created_at
                FROM decisions
                WHERE case_id = {case_id:String}
                ORDER BY created_at DESC
                LIMIT 1
                """,
                parameters={"case_id": case_id},
            )
        if not decision_rows:
            if approval.run_id:
                raise HTTPException(status_code=404, detail=f"Case '{case_id}' has no decision in run '{approval.run_id}'")
            raise HTTPException(status_code=404, detail=f"Case '{case_id}' has no decision")

        decision_row = decision_rows[0]
        run_id = decision_row.get("run_id", "")
        eligible = bool(int(decision_row.get("eligible_for_review", 0)))

        if approval.decision == ApprovalDecision.approve and not eligible:
            raise HTTPException(status_code=400, detail="Case is not eligible for human review approval")

        status = _decision_to_status(approval.decision)
        dispatch_payload: dict[str, Any] = {"dispatched": False, "reason": "not_approved"}

        if status == ApprovalStatus.approved.value:
            try:
                dispatch_payload = await self.dispatch_manager.dispatch_if_approved(
                    case_id=case_id,
                    decision_payload=decision_row,
                    approval_status=status,
                    notes=approval.notes,
                )
            except Exception as exc:
                LOGGER.exception("Dispatch failed for case %s", case_id)
                dispatch_payload = {"dispatched": False, "reason": "dispatch_error", "error": str(exc)}

        self.clickhouse.insert(
            table="approvals",
            rows=[
                [
                    case_id,
                    run_id,
                    status,
                    approval.reviewer_name,
                    approval.notes or "",
                    json.dumps(dispatch_payload, default=str),
                ]
            ],
            column_names=["case_id", "run_id", "status", "reviewer_name", "notes", "dispatch_json"],
        )

        log_audit_event(
            clickhouse=self.clickhouse,
            run_id=run_id,
            case_id=case_id,
            event_type="approval_updated",
            actor=approval.reviewer_name or "reviewer",
            payload={
                "decision": approval.decision.value,
                "status": status,
                "notes": approval.notes,
                "dispatch": dispatch_payload,
            },
        )

        return ApprovalResponse(case_id=case_id, status=ApprovalStatus(status), dispatch=dispatch_payload)

    async def execute_suggestion(self, case_id: str, request: SuggestionExecuteRequest) -> SuggestionExecuteResponse:
        """Execute the AI-generated suggestion for a case ('Do it' button)."""
        # Fetch the latest decision for this case
        if request.run_id:
            decision_rows = self.clickhouse.query_dicts(
                """
                SELECT run_id, case_id, severity, confidence, rationale, suggestion
                FROM decisions
                WHERE case_id = {case_id:String} AND run_id = {run_id:String}
                ORDER BY created_at DESC
                LIMIT 1
                """,
                parameters={"case_id": case_id, "run_id": request.run_id},
            )
        else:
            decision_rows = self.clickhouse.query_dicts(
                """
                SELECT run_id, case_id, severity, confidence, rationale, suggestion
                FROM decisions
                WHERE case_id = {case_id:String}
                ORDER BY created_at DESC
                LIMIT 1
                """,
                parameters={"case_id": case_id},
            )

        if not decision_rows:
            raise HTTPException(status_code=404, detail=f"No decision found for case '{case_id}'")

        decision_row = decision_rows[0]
        run_id = str(decision_row.get("run_id", ""))
        suggestion = str(decision_row.get("suggestion", ""))

        if not suggestion:
            raise HTTPException(status_code=400, detail=f"No suggestion available for case '{case_id}'")

        # Dispatch the suggestion via voice + email
        dispatch_payload: dict[str, Any] = {"dispatched": False, "reason": "suggestion_execution"}
        try:
            dispatch_payload = await self.dispatch_manager.dispatch_if_approved(
                case_id=case_id,
                decision_payload={**decision_row, "suggestion": suggestion},
                approval_status=ApprovalStatus.approved.value,
                notes=f"[Suggestion executed] {suggestion}",
            )
            dispatch_payload["suggestion_executed"] = True
        except Exception as exc:
            LOGGER.exception("Suggestion dispatch failed for case %s", case_id)
            dispatch_payload = {
                "dispatched": False,
                "suggestion_executed": False,
                "reason": "dispatch_error",
                "error": str(exc),
            }

        # Record the execution
        self.clickhouse.insert(
            table="suggestion_executions",
            rows=[
                [
                    case_id,
                    run_id,
                    suggestion,
                    request.operator_name,
                    request.notes,
                    json.dumps(dispatch_payload, default=str),
                ]
            ],
            column_names=["case_id", "run_id", "suggestion", "operator_name", "notes", "dispatch_json"],
        )

        log_audit_event(
            clickhouse=self.clickhouse,
            run_id=run_id,
            case_id=case_id,
            event_type="suggestion_executed",
            actor=request.operator_name or "operator",
            payload={
                "suggestion": suggestion,
                "dispatch": dispatch_payload,
                "notes": request.notes,
            },
        )

        return SuggestionExecuteResponse(
            case_id=case_id,
            suggestion=suggestion,
            executed=dispatch_payload.get("dispatched", False) or dispatch_payload.get("suggestion_executed", False),
            dispatch=dispatch_payload,
        )

    async def _execute_run(self, run_id: str, selected_cases: list[dict[str, Any]], started_at: datetime) -> None:
        metrics_inputs: list[CaseMetricInput] = []
        fusion_state = self._load_latest_fusion_state()
        strategy_hints = self._load_recent_strategy_notes()

        try:
            for idx, case_dict in enumerate(selected_cases, start=1):
                case = RawCaseInput.model_validate(case_dict)
                log_audit_event(
                    clickhouse=self.clickhouse,
                    run_id=run_id,
                    case_id=case.case_id,
                    event_type="case_processing_started",
                    actor="system",
                    payload={"position": idx},
                )

                ingest_output = await self.ingest_agent.run(
                    payload={"case": case.model_dump(mode="json")},
                    rag_context=None,
                    strategy_notes=strategy_hints,
                )
                normalized_case = ingest_output.normalized_case

                embedding_text = case_to_embedding_text(normalized_case)
                case_embedding = self.embedder.embed_text(embedding_text)

                self._insert_case_record(
                    run_id=run_id,
                    case=case,
                    normalized_case=normalized_case,
                    embedding=case_embedding,
                )

                rag_context = self.retriever.retrieve(
                    case_id=case.case_id,
                    normalized_case=normalized_case,
                    query_embedding=case_embedding,
                )
                log_audit_event(
                    clickhouse=self.clickhouse,
                    run_id=run_id,
                    case_id=case.case_id,
                    event_type="rag_context_built",
                    actor="system",
                    payload=rag_context,
                )

                # Run genomics + epi_osint in parallel (they're independent)
                genomics_output, epi_output = await asyncio.gather(
                    self.genomics_agent.run(
                        payload={
                            "case": normalized_case,
                            "ingest_output": ingest_output.model_dump(),
                        },
                        rag_context=rag_context,
                        strategy_notes=strategy_hints,
                    ),
                    self.epi_agent.run(
                        payload={
                            "case": normalized_case,
                            "ingest_output": ingest_output.model_dump(),
                        },
                        rag_context=rag_context,
                        strategy_notes=strategy_hints,
                    ),
                )
                meta_output = await self.meta_agent.run(
                    payload={
                        "case": normalized_case,
                        "ingest_output": ingest_output.model_dump(),
                        "genomics_output": genomics_output.model_dump(),
                        "epi_output": epi_output.model_dump(),
                        "fusion_state": fusion_state.model_dump(),
                    },
                    rag_context=rag_context,
                    strategy_notes=strategy_hints,
                )

                eligible = (
                    meta_output.severity >= self.settings.guardrail_severity_threshold
                    and meta_output.confidence_pct >= self.settings.guardrail_confidence_threshold_pct
                )

                self._insert_agent_outputs(
                    run_id=run_id,
                    case_id=case.case_id,
                    ingest_output=ingest_output.model_dump(),
                    genomics_output=genomics_output.model_dump(),
                    epi_output=epi_output.model_dump(),
                    meta_output=meta_output.model_dump(),
                )

                self.clickhouse.insert(
                    table="decisions",
                    rows=[
                        [
                            run_id,
                            case.case_id,
                            meta_output.fused_score,
                            meta_output.severity,
                            meta_output.confidence_pct,
                            1 if eligible else 0,
                            meta_output.rationale,
                            json.dumps(meta_output.contributions.model_dump()),
                            fusion_state.threshold,
                            meta_output.suggestion,
                        ]
                    ],
                    column_names=[
                        "run_id",
                        "case_id",
                        "fused_score",
                        "severity",
                        "confidence",
                        "eligible_for_review",
                        "rationale",
                        "contributions_json",
                        "threshold",
                        "suggestion",
                    ],
                )

                initial_status = ApprovalStatus.pending.value if eligible else ApprovalStatus.not_required.value
                self.clickhouse.insert(
                    table="approvals",
                    rows=[
                        [
                            case.case_id,
                            run_id,
                            initial_status,
                            None,
                            "auto-created by guardrail",
                            json.dumps({"dispatched": False, "reason": "approval_required"}),
                        ]
                    ],
                    column_names=["case_id", "run_id", "status", "reviewer_name", "notes", "dispatch_json"],
                )

                component_scores = {
                    "genomics": genomics_output.genomics_score,
                    "epi": epi_output.epi_score,
                    "geo": epi_output.geo_score,
                }
                predicted_positive = bool(eligible)

                new_fusion_state = update_fusion_state(
                    current=fusion_state,
                    component_scores=component_scores,
                    predicted_severity=meta_output.severity,
                    predicted_confidence_pct=meta_output.confidence_pct,
                    ground_truth_true=case.ground_truth.true_outbreak,
                    true_severity=case.ground_truth.true_severity,
                )

                strategy_note, prompt_updates = build_strategy_update(
                    predicted_positive=predicted_positive,
                    ground_truth_true=case.ground_truth.true_outbreak,
                    component_scores=component_scores,
                    meta_strategy_notes=meta_output.strategy_notes,
                )
                merged_prompts = {**meta_output.updated_prompts, **prompt_updates}
                strategy_embedding = self.embedder.embed_text(strategy_note + " " + json.dumps(merged_prompts, default=str))

                self.clickhouse.insert(
                    table="strategy_memory",
                    rows=[
                        [
                            run_id,
                            case.case_id,
                            strategy_note,
                            json.dumps(merged_prompts),
                            json.dumps(
                                {
                                    "w_genomics": new_fusion_state.w_genomics,
                                    "w_epi": new_fusion_state.w_epi,
                                    "w_geo": new_fusion_state.w_geo,
                                }
                            ),
                            new_fusion_state.threshold,
                            strategy_embedding,
                        ]
                    ],
                    column_names=[
                        "run_id",
                        "case_id",
                        "strategy_notes",
                        "updated_prompts_json",
                        "weights_json",
                        "threshold",
                        "embedding",
                    ],
                )
                log_audit_event(
                    clickhouse=self.clickhouse,
                    run_id=run_id,
                    case_id=case.case_id,
                    event_type="strategy_memory_updated",
                    actor="system",
                    payload={
                        "strategy_notes": strategy_note,
                        "weights": {
                            "w_genomics": new_fusion_state.w_genomics,
                            "w_epi": new_fusion_state.w_epi,
                            "w_geo": new_fusion_state.w_geo,
                        },
                        "threshold": new_fusion_state.threshold,
                    },
                )

                metrics_inputs.append(
                    CaseMetricInput(
                        case_date=case.date,
                        official_alert_date=case.ground_truth.official_alert_date,
                        predicted_positive=predicted_positive,
                        ground_truth_true=case.ground_truth.true_outbreak,
                        predicted_severity=meta_output.severity,
                        true_severity=case.ground_truth.true_severity,
                        confidence_pct=meta_output.confidence_pct,
                    )
                )

                fusion_state = new_fusion_state
                strategy_hints = [strategy_note, *strategy_hints][:5]

                self._run_status[run_id] = RunStatusResponse(
                    run_id=run_id,
                    status="running",
                    processed=idx,
                    total=len(selected_cases),
                    started_at=started_at,
                    ended_at=None,
                    error=None,
                )
                self._insert_run_event(
                    run_id=run_id,
                    status="running",
                    started_at=started_at,
                    ended_at=None,
                    processed=idx,
                    total=len(selected_cases),
                    error=None,
                    config={},
                )

            metrics = compute_run_metrics(metrics_inputs)
            self.clickhouse.insert(
                table="metrics",
                rows=[
                    [
                        run_id,
                        metrics["lead_time_days"],
                        metrics["false_alarm_rate"],
                        metrics["severity_mae"],
                        metrics["brier_score"],
                    ]
                ],
                column_names=["run_id", "lead_time_days", "false_alarm_rate", "severity_mae", "brier_score"],
            )

            ended = datetime.utcnow()
            self._run_status[run_id] = RunStatusResponse(
                run_id=run_id,
                status="completed",
                processed=len(selected_cases),
                total=len(selected_cases),
                started_at=started_at,
                ended_at=ended,
                error=None,
            )
            self._insert_run_event(
                run_id=run_id,
                status="completed",
                started_at=started_at,
                ended_at=ended,
                processed=len(selected_cases),
                total=len(selected_cases),
                error=None,
                config={},
            )
            log_audit_event(
                clickhouse=self.clickhouse,
                run_id=run_id,
                case_id=None,
                event_type="run_completed",
                actor="system",
                payload=metrics,
            )
        except Exception as exc:
            LOGGER.exception("Run %s failed", run_id)
            ended = datetime.utcnow()
            self._run_status[run_id] = RunStatusResponse(
                run_id=run_id,
                status="failed",
                processed=self._run_status[run_id].processed,
                total=len(selected_cases),
                started_at=started_at,
                ended_at=ended,
                error=str(exc),
            )
            self._insert_run_event(
                run_id=run_id,
                status="failed",
                started_at=started_at,
                ended_at=ended,
                processed=self._run_status[run_id].processed,
                total=len(selected_cases),
                error=str(exc),
                config={},
            )
            log_audit_event(
                clickhouse=self.clickhouse,
                run_id=run_id,
                case_id=None,
                event_type="run_failed",
                actor="system",
                payload={"error": str(exc)},
            )

    def _insert_case_record(
        self,
        run_id: str,
        case: RawCaseInput,
        normalized_case: dict[str, Any],
        embedding: list[float],
    ) -> None:
        self.clickhouse.insert(
            table="cases",
            rows=[
                [
                    case.case_id,
                    run_id,
                    case.date,
                    case.country,
                    case.city,
                    case.lat,
                    case.lon,
                    case.pathogen_label,
                    json.dumps(normalized_case, default=str),
                    json.dumps(case.ground_truth.model_dump(mode="json"), default=str),
                    [float(v) for v in embedding],
                ]
            ],
            column_names=[
                "case_id",
                "run_id",
                "case_date",
                "country",
                "city",
                "lat",
                "lon",
                "pathogen_label",
                "normalized_json",
                "ground_truth_json",
                "embedding",
            ],
        )

    def _insert_agent_outputs(
        self,
        run_id: str,
        case_id: str,
        ingest_output: dict[str, Any],
        genomics_output: dict[str, Any],
        epi_output: dict[str, Any],
        meta_output: dict[str, Any],
    ) -> None:
        rows = [
            [run_id, case_id, "ingest", json.dumps(ingest_output, default=str), ingest_output.get("score", 0.0), ingest_output.get("confidence", 0.0)],
            [run_id, case_id, "genomics", json.dumps(genomics_output, default=str), genomics_output.get("genomics_score", 0.0), genomics_output.get("confidence", 0.0)],
            [run_id, case_id, "epi_osint", json.dumps(epi_output, default=str), epi_output.get("epi_score", 0.0), epi_output.get("confidence", 0.0)],
            [run_id, case_id, "meta", json.dumps(meta_output, default=str), meta_output.get("severity", 0.0), meta_output.get("confidence_pct", 0.0) / 100.0],
        ]
        self.clickhouse.insert(
            table="agent_outputs",
            rows=rows,
            column_names=["run_id", "case_id", "agent_name", "output_json", "score", "confidence"],
        )

    def _insert_run_event(
        self,
        run_id: str,
        status: str,
        started_at: datetime,
        ended_at: datetime | None,
        processed: int,
        total: int,
        error: str | None,
        config: dict[str, Any],
    ) -> None:
        self.clickhouse.insert(
            table="runs",
            rows=[
                [
                    run_id,
                    status,
                    started_at,
                    ended_at,
                    json.dumps(config, default=str),
                    error,
                    int(processed),
                    int(total),
                ]
            ],
            column_names=["run_id", "status", "started_at", "ended_at", "config_json", "error", "processed", "total"],
        )

    def _load_synthetic_cases(self) -> list[dict[str, Any]]:
        """Load cases from combined outbreaks.jsonl or combine from 4 sources on the fly."""
        data_path = _resolve_data_path(self.settings.outbreak_data_path)

        # Try running the combiner first (4 source files → outbreaks.jsonl)
        if not data_path.exists():
            data_path = self._try_combine_sources(data_path)

        if not data_path.exists():
            raise RuntimeError(f"Synthetic dataset not found: {data_path}")

        cases: list[dict[str, Any]] = []
        with data_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                case = RawCaseInput.model_validate_json(line)
                cases.append(case.model_dump(mode="json"))

        LOGGER.info("Loaded %s synthetic cases from %s", len(cases), data_path)
        return cases

    @staticmethod
    def _try_combine_sources(outbreaks_path: Path) -> Path:
        """Attempt to combine 4 source JSONL files into outbreaks.jsonl."""
        data_dir = outbreaks_path.parent
        source_files = [
            "genomic_feeds.jsonl", "osint_health.jsonl",
            "sns_search.jsonl", "geospatial.jsonl", "ground_truth.jsonl",
        ]
        if all((data_dir / f).exists() for f in source_files):
            try:
                import importlib.util
                combine_path = data_dir / "combine.py"
                if combine_path.exists():
                    spec = importlib.util.spec_from_file_location("combine", combine_path)
                    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
                    spec.loader.exec_module(mod)  # type: ignore[union-attr]
                    cases = mod.combine()
                    mod.write_outbreaks(cases, outbreaks_path)
                    LOGGER.info(
                        "Auto-combined %d cases from source files → %s",
                        len(cases), outbreaks_path,
                    )
            except Exception:
                LOGGER.exception("Failed to auto-combine source files")
        return outbreaks_path

    def _load_latest_fusion_state(self) -> FusionState:
        rows = self.clickhouse.query_dicts(
            """
            SELECT weights_json, threshold, created_at
            FROM strategy_memory
            ORDER BY created_at DESC
            LIMIT 1
            """
        )
        if not rows:
            return default_fusion_state()

        row = rows[0]
        payload = {
            "weights": _loads_json(row.get("weights_json")),
            "threshold": row.get("threshold"),
        }
        return fusion_state_from_memory_row(payload)

    def _load_recent_strategy_notes(self) -> list[str]:
        rows = self.clickhouse.query_dicts(
            """
            SELECT strategy_notes
            FROM strategy_memory
            ORDER BY created_at DESC
            LIMIT 5
            """
        )
        return [str(row.get("strategy_notes", "")).strip() for row in rows if str(row.get("strategy_notes", "")).strip()]


def _resolve_data_path(config_path: str) -> Path:
    candidate = Path(config_path)
    if candidate.is_absolute():
        return candidate
    backend_root = Path(__file__).resolve().parents[1]
    return (backend_root / config_path).resolve()


def _decision_to_status(decision: ApprovalDecision) -> str:
    if decision == ApprovalDecision.approve:
        return ApprovalStatus.approved.value
    if decision == ApprovalDecision.reject:
        return ApprovalStatus.rejected.value
    return ApprovalStatus.request_more_evidence.value


def _latest_by_case_run(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    latest: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        case_id = str(row.get("case_id", "")).strip()
        run_id = str(row.get("run_id", "")).strip()
        if not case_id:
            continue
        key = (case_id, run_id)
        if key not in latest:
            latest[key] = row
    return latest


def _loads_json(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if value is None:
        return {}
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}
