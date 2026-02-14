from __future__ import annotations

from app.improve.update import default_fusion_state, update_fusion_state


def test_weight_update_keeps_weights_normalized() -> None:
    state = default_fusion_state()
    updated = update_fusion_state(
        current=state,
        component_scores={"genomics": 8.5, "epi": 7.8, "geo": 4.2},
        predicted_severity=8.0,
        predicted_confidence_pct=78.0,
        ground_truth_true=True,
        true_severity=9.0,
    )
    total = updated.w_genomics + updated.w_epi + updated.w_geo
    assert abs(total - 1.0) < 1e-6


def test_threshold_moves_up_on_false_positive() -> None:
    state = default_fusion_state()
    updated = update_fusion_state(
        current=state,
        component_scores={"genomics": 7.5, "epi": 7.0, "geo": 7.0},
        predicted_severity=8.0,
        predicted_confidence_pct=80.0,
        ground_truth_true=False,
        true_severity=2.0,
    )
    assert updated.threshold > state.threshold
