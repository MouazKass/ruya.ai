from __future__ import annotations

from statistics import mean

from app.models import CaseMetricInput


def compute_run_metrics(items: list[CaseMetricInput]) -> dict[str, float]:
    if not items:
        return {
            "lead_time_days": 0.0,
            "false_alarm_rate": 0.0,
            "severity_mae": 0.0,
            "brier_score": 0.0,
        }

    lead_times: list[float] = []
    false_positives = 0
    predicted_positives = 0
    severity_errors: list[float] = []
    brier_values: list[float] = []

    for item in items:
        if item.predicted_positive:
            predicted_positives += 1
            if item.ground_truth_true:
                lead_times.append(float((item.official_alert_date - item.case_date).days))
            else:
                false_positives += 1

        severity_errors.append(abs(item.predicted_severity - item.true_severity))

        target = 1.0 if item.ground_truth_true else 0.0
        prob = item.confidence_pct / 100.0
        brier_values.append((prob - target) ** 2)

    false_alarm_rate = float(false_positives / predicted_positives) if predicted_positives else 0.0

    return {
        "lead_time_days": float(mean(lead_times)) if lead_times else 0.0,
        "false_alarm_rate": false_alarm_rate,
        "severity_mae": float(mean(severity_errors)),
        "brier_score": float(mean(brier_values)),
    }
