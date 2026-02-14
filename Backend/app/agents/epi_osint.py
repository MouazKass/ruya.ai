from __future__ import annotations

from typing import Any

from app.agents.base import AgentBase
from app.config import Settings
from app.models import EpiOsintOutput


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


class EpiOsintAgent(AgentBase):
    def __init__(self, settings: Settings) -> None:
        super().__init__(settings=settings, agent_name="epi_osint", prompt_file="epi_osint.txt", output_model=EpiOsintOutput)

    def local_fallback(
        self,
        payload: dict[str, Any],
        rag_context: dict[str, Any] | None,
        strategy_notes: list[str] | None,
    ) -> dict[str, Any]:
        case = payload.get("case", {})
        epi = case.get("epi_osint", {})
        geo = case.get("geo", {})

        anomaly = float(epi.get("anomaly_score", 0.0))
        reliability = float(epi.get("reliability_hint", 0.0))
        source_types = epi.get("source_types", []) or []

        source_diversity = _clamp(len(set(source_types)) / 4.0, 0.0, 1.0)
        signal_to_noise = round(_clamp(0.65 * reliability + 0.35 * source_diversity, 0.0, 1.0), 3)

        epi_score = (0.6 * anomaly + 0.25 * reliability + 0.15 * source_diversity) * 10.0
        epi_score = round(_clamp(epi_score, 0.0, 10.0), 3)

        geo_score = (
            float(geo.get("travel_hub_score", 0.0)) * 0.4
            + float(geo.get("population_density_score", 0.0)) * 0.35
            + float(geo.get("border_connectivity", 0.0)) * 0.25
        ) * 10.0
        geo_score = round(_clamp(geo_score, 0.0, 10.0), 3)

        confidence = round(_clamp(0.45 + 0.45 * signal_to_noise, 0.0, 1.0), 3)

        noise_flags: list[str] = []
        if reliability < 0.4:
            noise_flags.append("low_reliability_sources")
        if source_diversity < 0.25:
            noise_flags.append("single_source_bias")

        evidence = [
            f"anomaly_score={round(anomaly, 3)}",
            f"reliability_hint={round(reliability, 3)}",
            f"source_diversity={round(source_diversity, 3)}",
            f"travel_hub_score={round(float(geo.get('travel_hub_score', 0.0)), 3)}",
        ]

        return {
            "epi_score": epi_score,
            "geo_score": geo_score,
            "signal_to_noise": signal_to_noise,
            "confidence": confidence,
            "evidence": evidence,
            "noise_flags": noise_flags,
        }
