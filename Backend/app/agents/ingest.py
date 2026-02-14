from __future__ import annotations

from typing import Any

from app.agents.base import AgentBase
from app.config import Settings
from app.models import IngestOutput


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


class IngestAgent(AgentBase):
    def __init__(self, settings: Settings) -> None:
        super().__init__(settings=settings, agent_name="ingest", prompt_file="ingest.txt", output_model=IngestOutput)

    def local_fallback(
        self,
        payload: dict[str, Any],
        rag_context: dict[str, Any] | None,
        strategy_notes: list[str] | None,
    ) -> dict[str, Any]:
        case = payload.get("case", {})
        genomic = case.get("genomic", {})
        epi = case.get("epi_osint", {})
        geo = case.get("geo", {})

        source_types = epi.get("source_types", []) or []
        news = epi.get("news_snippets", []) or []

        source_diversity = _clamp(len(set(source_types)) / 4.0, 0.0, 1.0)
        news_volume = _clamp(len(news) / 5.0, 0.0, 1.0)
        reliability = float(epi.get("reliability_hint", 0.5))

        credibility = _clamp(0.55 * reliability + 0.25 * source_diversity + 0.20 * news_volume, 0.0, 1.0)

        genomic_pressure = (
            float(genomic.get("mutation_novelty", 0.0)) * 0.5
            + float(genomic.get("lineage_deviation", 0.0)) * 0.35
            + (0.15 if bool(genomic.get("recombination_flag", False)) else 0.0)
        )
        geo_pressure = (
            float(geo.get("travel_hub_score", 0.0))
            + float(geo.get("population_density_score", 0.0))
            + float(geo.get("border_connectivity", 0.0))
        ) / 3.0
        risk_signal = (
            0.4 * genomic_pressure
            + 0.35 * float(epi.get("anomaly_score", 0.0))
            + 0.25 * geo_pressure
        )

        score = round(_clamp(risk_signal, 0.0, 1.0) * 10.0, 3)
        confidence = round(_clamp(0.5 + 0.45 * credibility, 0.0, 1.0), 3)

        normalized_case = {
            **case,
            "credibility_score": round(credibility, 3),
            "derived_geo_pressure": round(geo_pressure, 3),
            "derived_genomic_pressure": round(genomic_pressure, 3),
        }

        evidence = [
            f"reliability_hint={round(reliability, 3)}",
            f"source_diversity={round(source_diversity, 3)}",
            f"anomaly_score={round(float(epi.get('anomaly_score', 0.0)), 3)}",
        ]

        return {
            "normalized_case": normalized_case,
            "credibility_score": round(credibility, 3),
            "score": score,
            "confidence": confidence,
            "evidence": evidence,
        }
