from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.models import ApprovalRequest, RawCaseInput


VALID_CASE = {
    "case_id": "CASE-TEST-001",
    "country": "Kenya",
    "city": "Nairobi",
    "lat": -1.286389,
    "lon": 36.817223,
    "date": "2025-01-11",
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
        "official_alert_date": "2025-01-22",
    },
}


def test_raw_case_schema_validation_passes() -> None:
    model = RawCaseInput.model_validate(VALID_CASE)
    assert model.case_id == "CASE-TEST-001"
    assert model.ground_truth.true_outbreak is True


def test_raw_case_schema_validation_rejects_missing_required_field() -> None:
    invalid = dict(VALID_CASE)
    invalid.pop("geo")
    with pytest.raises(ValidationError):
        RawCaseInput.model_validate(invalid)


def test_approval_request_rejects_invalid_decision() -> None:
    with pytest.raises(ValidationError):
        ApprovalRequest.model_validate({"decision": "ship_it"})
