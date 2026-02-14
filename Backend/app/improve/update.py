from __future__ import annotations

from typing import Any

from app.models import FusionState


def default_fusion_state() -> FusionState:
    return FusionState(w_genomics=0.4, w_epi=0.4, w_geo=0.2, threshold=0.7)


def update_fusion_state(
    current: FusionState,
    component_scores: dict[str, float],
    predicted_severity: float,
    predicted_confidence_pct: float,
    ground_truth_true: bool,
    true_severity: float,
    learning_rate: float = 0.08,
) -> FusionState:
    weights = {
        "genomics": current.w_genomics,
        "epi": current.w_epi,
        "geo": current.w_geo,
    }

    weighted_pred = (
        weights["genomics"] * component_scores.get("genomics", 0.0)
        + weights["epi"] * component_scores.get("epi", 0.0)
        + weights["geo"] * component_scores.get("geo", 0.0)
    )
    error = (true_severity - weighted_pred) / 10.0

    updated: dict[str, float] = {}
    for key, weight in weights.items():
        direction = (component_scores.get(key, 0.0) - weighted_pred) / 10.0
        next_weight = weight + learning_rate * error * direction
        updated[key] = min(0.9, max(0.05, next_weight))

    total = sum(updated.values()) or 1.0
    normalized = {k: v / total for k, v in updated.items()}

    predicted_positive = predicted_severity >= (current.threshold * 10.0) and predicted_confidence_pct >= 60.0
    new_threshold = current.threshold
    if predicted_positive and not ground_truth_true:
        new_threshold += 0.01
    if (not predicted_positive) and ground_truth_true and true_severity >= 7.0:
        new_threshold -= 0.01
    new_threshold = min(0.85, max(0.4, new_threshold))

    return FusionState(
        w_genomics=normalized["genomics"],
        w_epi=normalized["epi"],
        w_geo=normalized["geo"],
        threshold=new_threshold,
    )


def build_strategy_update(
    predicted_positive: bool,
    ground_truth_true: bool,
    component_scores: dict[str, float],
    meta_strategy_notes: str,
) -> tuple[str, dict[str, str]]:
    dominant_signal = max(component_scores.items(), key=lambda pair: pair[1])[0]

    if predicted_positive and not ground_truth_true:
        note = "Reduce false alarms by down-weighting low reliability OSINT anomalies."
    elif (not predicted_positive) and ground_truth_true:
        note = "Improve sensitivity for early outbreak indicators, especially recombination plus travel pressure."
    else:
        note = "Preserve current strategy and continue calibration on confidence signals."

    merged_note = f"{note} Dominant signal: {dominant_signal}. {meta_strategy_notes}".strip()
    updates = {
        "ingest": "Prioritize source reliability calibration and keep normalization strict.",
        "genomics": "Highlight lineage deviation and recombination when novelty is rising.",
        "epi_osint": "Penalize noisy stories lacking source diversity.",
        "meta": "State weighted contribution and confidence rationale in concise JSON.",
    }
    return merged_note, updates


def fusion_state_from_memory_row(row: dict[str, Any] | None) -> FusionState:
    if not row:
        return default_fusion_state()

    weights = row.get("weights") or {}
    try:
        return FusionState(
            w_genomics=float(weights.get("w_genomics", 0.4)),
            w_epi=float(weights.get("w_epi", 0.4)),
            w_geo=float(weights.get("w_geo", 0.2)),
            threshold=float(row.get("threshold", 0.7)),
        )
    except Exception:
        return default_fusion_state()
