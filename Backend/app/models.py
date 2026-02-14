from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True, str_strip_whitespace=True)


# ---------------------------------------------------------------------------
# Source-level signal models (one per input-source JSONL file)
# ---------------------------------------------------------------------------

class GenomicFeedSignal(StrictModel):
    """Single record from genomic_feeds.jsonl (GISAID / NCBI GenBank)."""
    signal_id: str
    event_id: str
    source: str  # gisaid | ncbi_genbank
    timestamp: datetime
    country: str
    city: str
    lat: float
    lon: float
    pathogen: str | None = None
    lineage: str | None = None
    mutation_novelty: float = Field(ge=0, le=1)
    lineage_deviation: float = Field(ge=0, le=1)
    recombination_flag: bool
    sequence_count: int = Field(ge=0)
    notes: str


class OsintHealthSignal(StrictModel):
    """Single record from osint_health.jsonl (WHO DON / ProMED / News API / etc.)."""
    signal_id: str
    event_id: str
    source: str  # who_don | promed | news_api | who_bulletin | hospital_report
    timestamp: datetime
    country: str
    city: str
    lat: float
    lon: float
    pathogen_mention: str | None = None
    headline: str
    snippet: str
    anomaly_score: float = Field(ge=0, le=1)
    reliability: float = Field(ge=0, le=1)
    case_count_mentioned: int | None = None


class SnsSearchSignal(StrictModel):
    """Single record from sns_search.jsonl (Social Media / Forums / Google Trends)."""
    signal_id: str
    event_id: str
    source: str  # social_media | forum | google_trends | local_press
    timestamp: datetime
    country: str
    city: str
    lat: float
    lon: float
    keyword: str
    mention_count: int = Field(ge=0)
    sentiment_negative_pct: float = Field(ge=0, le=1)
    trend_velocity: float = Field(ge=0)
    snippet: str
    reliability_hint: float = Field(ge=0, le=1)


class GeospatialSignal(StrictModel):
    """Single record from geospatial.jsonl (Flights / OSM / Pop Density)."""
    signal_id: str
    event_id: str
    source: str  # flight_data | osm_geospatial | pop_density
    timestamp: datetime
    country: str
    city: str
    lat: float
    lon: float
    travel_hub_score: float = Field(ge=0, le=1)
    population_density_score: float = Field(ge=0, le=1)
    border_connectivity: float = Field(ge=0, le=1)
    notes: str


class EventGroundTruth(StrictModel):
    """Single record from ground_truth.jsonl."""
    event_id: str
    country: str
    city: str
    lat: float
    lon: float
    case_date: date
    pathogen_label: str | None = None
    true_outbreak: bool
    true_severity: float = Field(ge=0, le=10)
    official_alert_date: date


# ---------------------------------------------------------------------------
# Combined canonical models (produced by combine.py)
# ---------------------------------------------------------------------------

class GenomicFeatures(StrictModel):
    mutation_novelty: float = Field(ge=0, le=1)
    lineage_deviation: float = Field(ge=0, le=1)
    recombination_flag: bool
    notes: str


class EpiOsintFeatures(StrictModel):
    news_snippets: list[str]
    source_types: list[str]
    anomaly_score: float = Field(ge=0, le=1)
    reliability_hint: float = Field(ge=0, le=1)


class GeoFeatures(StrictModel):
    travel_hub_score: float = Field(ge=0, le=1)
    population_density_score: float = Field(ge=0, le=1)
    border_connectivity: float = Field(ge=0, le=1)


class GroundTruth(StrictModel):
    true_outbreak: bool
    true_severity: float = Field(ge=0, le=10)
    official_alert_date: date


class RawCaseInput(StrictModel):
    case_id: str
    country: str
    city: str
    lat: float
    lon: float
    date: date
    pathogen_label: str | None = None
    genomic: GenomicFeatures
    epi_osint: EpiOsintFeatures
    geo: GeoFeatures
    ground_truth: GroundTruth


class IngestOutput(StrictModel):
    normalized_case: dict[str, Any]
    credibility_score: float = Field(ge=0, le=1)
    score: float = Field(ge=0, le=10)
    confidence: float = Field(ge=0, le=1)
    evidence: list[str]


class GenomicsOutput(StrictModel):
    genomics_score: float = Field(ge=0, le=10)
    confidence: float = Field(ge=0, le=1)
    risk_band: str
    evidence: list[str]


class EpiOsintOutput(StrictModel):
    epi_score: float = Field(ge=0, le=10)
    geo_score: float = Field(ge=0, le=10)
    signal_to_noise: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    evidence: list[str]
    noise_flags: list[str]


class ContributionScores(StrictModel):
    genomics: float = Field(ge=0, le=10)
    epi: float = Field(ge=0, le=10)
    geo: float = Field(ge=0, le=10)


class MetaOutput(StrictModel):
    fused_score: float = Field(ge=0, le=10)
    severity: float = Field(ge=0, le=10)
    confidence_pct: float = Field(ge=0, le=100)
    rationale: str
    contributions: ContributionScores
    recommended_action: str
    strategy_notes: str
    updated_prompts: dict[str, str]


class ApprovalStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    request_more_evidence = "request_more_evidence"
    not_required = "not_required"


class ApprovalDecision(str, Enum):
    approve = "approve"
    reject = "reject"
    request_more_evidence = "request_more_evidence"


class ApprovalRequest(StrictModel):
    decision: ApprovalDecision
    run_id: str | None = None
    reviewer_name: str | None = None
    notes: str | None = None


class ApprovalResponse(StrictModel):
    case_id: str
    status: ApprovalStatus
    dispatch: dict[str, Any]


class StartRunRequest(StrictModel):
    num_cases: int = Field(default=20, ge=1, le=500)


class StartRunResponse(StrictModel):
    run_id: str
    status: str


class RunStatusResponse(StrictModel):
    run_id: str
    status: str
    processed: int
    total: int
    started_at: datetime
    ended_at: datetime | None = None
    error: str | None = None


class CaseSummary(StrictModel):
    case_id: str
    run_id: str
    country: str
    city: str
    date: date
    status: ApprovalStatus | str
    severity: float
    confidence: float
    eligible_for_review: bool


class DashboardResponse(StrictModel):
    recent_cases: list[CaseSummary]
    current_run_metrics: dict[str, Any]
    pending_approvals_queue: list[dict[str, Any]]
    case_details_summary: list[dict[str, Any]]


class CaseDetailResponse(StrictModel):
    case: dict[str, Any]
    rag_context_sources: dict[str, Any]
    agent_outputs: list[dict[str, Any]]
    decision: dict[str, Any] | None
    approvals: list[dict[str, Any]]
    audit_trail: list[dict[str, Any]]


class FusionState(StrictModel):
    w_genomics: float = Field(gt=0)
    w_epi: float = Field(gt=0)
    w_geo: float = Field(gt=0)
    threshold: float = Field(ge=0.4, le=0.85)

    @model_validator(mode="after")
    def _weights_must_sum(self) -> "FusionState":
        total = self.w_genomics + self.w_epi + self.w_geo
        if total <= 0:
            raise ValueError("Fusion weights must be positive")
        return self


class CaseMetricInput(StrictModel):
    case_date: date
    official_alert_date: date
    predicted_positive: bool
    ground_truth_true: bool
    predicted_severity: float = Field(ge=0, le=10)
    true_severity: float = Field(ge=0, le=10)
    confidence_pct: float = Field(ge=0, le=100)
