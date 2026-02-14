from __future__ import annotations

from typing import Any

from app.agents.base import AgentBase
from app.config import Settings
from app.models import GenomicsOutput


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


class GenomicsAgent(AgentBase):
    def __init__(self, settings: Settings) -> None:
        super().__init__(settings=settings, agent_name="genomics", prompt_file="genomics.txt", output_model=GenomicsOutput)

    def local_fallback(
        self,
        payload: dict[str, Any],
        rag_context: dict[str, Any] | None,
        strategy_notes: list[str] | None,
    ) -> dict[str, Any]:
        case = payload.get("case", {})
        ingest_output = payload.get("ingest_output", {})
        genomic = case.get("genomic", {})

        novelty = float(genomic.get("mutation_novelty", 0.0))
        lineage = float(genomic.get("lineage_deviation", 0.0))
        recombination = 1.0 if bool(genomic.get("recombination_flag", False)) else 0.0

        score = (0.45 * novelty + 0.35 * lineage + 0.20 * recombination) * 10.0
        score = round(_clamp(score, 0.0, 10.0), 3)

        credibility = float(ingest_output.get("credibility_score", case.get("credibility_score", 0.5)))
        confidence = round(_clamp(0.5 + 0.4 * credibility, 0.0, 1.0), 3)

        if score >= 7.0:
            band = "high"
        elif score >= 4.0:
            band = "moderate"
        else:
            band = "low"

        evidence = [
            f"mutation_novelty={round(novelty, 3)}",
            f"lineage_deviation={round(lineage, 3)}",
            f"recombination_flag={bool(genomic.get('recombination_flag', False))}",
        ]

        return {
            "genomics_score": score,
            "confidence": confidence,
            "risk_band": band,
            "evidence": evidence,
        }
