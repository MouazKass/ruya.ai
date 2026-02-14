from __future__ import annotations

from typing import Any

from app.agents.base import AgentBase
from app.config import Settings
from app.models import MetaOutput


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


class MetaAgent(AgentBase):
    def __init__(self, settings: Settings) -> None:
        super().__init__(settings=settings, agent_name="meta", prompt_file="meta.txt", output_model=MetaOutput)

    def local_fallback(
        self,
        payload: dict[str, Any],
        rag_context: dict[str, Any] | None,
        strategy_notes: list[str] | None,
    ) -> dict[str, Any]:
        ingest = payload.get("ingest_output", {})
        genomics = payload.get("genomics_output", {})
        epi = payload.get("epi_output", {})
        fusion_state = payload.get("fusion_state", {})

        w_genomics = float(fusion_state.get("w_genomics", 0.4))
        w_epi = float(fusion_state.get("w_epi", 0.4))
        w_geo = float(fusion_state.get("w_geo", 0.2))

        genomics_score = float(genomics.get("genomics_score", 0.0))
        epi_score = float(epi.get("epi_score", 0.0))
        geo_score = float(epi.get("geo_score", 0.0))

        fused = (w_genomics * genomics_score) + (w_epi * epi_score) + (w_geo * geo_score)
        fused = round(_clamp(fused, 0.0, 10.0), 3)

        conf = (
            0.25 * float(ingest.get("confidence", 0.5))
            + 0.35 * float(genomics.get("confidence", 0.5))
            + 0.40 * float(epi.get("confidence", 0.5))
        )
        confidence_pct = round(_clamp(conf, 0.0, 1.0) * 100.0, 2)

        recommended_action = "eligible_for_review" if fused >= 7.0 and confidence_pct >= 60.0 else "monitor"

        top_signal = max(
            [
                ("genomics", genomics_score),
                ("epi", epi_score),
                ("geo", geo_score),
            ],
            key=lambda pair: pair[1],
        )[0]
        strategy = f"Prioritize {top_signal} signal handling; calibrate confidence around low-reliability OSINT."

        # Build a contextual 1-line actionable suggestion
        country = (payload.get("case") or {}).get("country", "the affected region")
        city = (payload.get("case") or {}).get("city", "")
        location_label = f"{city}, {country}" if city else country

        if fused >= 7.0 and confidence_pct >= 60.0:
            suggestion = f"Dispatch outbreak alert to regional health authority for {location_label}."
        elif fused >= 5.0:
            suggestion = f"Increase epidemiological surveillance cadence in {location_label}."
        elif top_signal == "genomics" and genomics_score >= 4.0:
            suggestion = f"Expand genomic sequencing coverage in {location_label} laboratories."
        else:
            suggestion = f"Continue routine monitoring for {location_label}; no immediate action required."

        rationale = (
            f"Fusion used weights genomics={w_genomics:.2f}, epi={w_epi:.2f}, geo={w_geo:.2f}. "
            f"Scores were genomics={genomics_score:.2f}, epi={epi_score:.2f}, geo={geo_score:.2f}."
        )

        return {
            "fused_score": fused,
            "severity": fused,
            "confidence_pct": confidence_pct,
            "rationale": rationale,
            "contributions": {
                "genomics": round(genomics_score, 3),
                "epi": round(epi_score, 3),
                "geo": round(geo_score, 3),
            },
            "recommended_action": recommended_action,
            "suggestion": suggestion,
            "strategy_notes": strategy,
            "updated_prompts": {
                "ingest": "Normalize signals and preserve credibility markers.",
                "genomics": "Emphasize recombination and lineage deviation shifts.",
                "epi_osint": "Filter low-reliability chatter before anomaly scoring.",
                "meta": "Explain weighted fusion and confidence traceability in JSON.",
            },
        }
