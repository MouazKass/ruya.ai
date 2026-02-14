"""Combine 4 source JSONL files + ground_truth into canonical outbreaks.jsonl.

Reads:
  genomic_feeds.jsonl   → GenomicFeatures
  osint_health.jsonl    → EpiOsintFeatures (official OSINT portion)
  sns_search.jsonl      → EpiOsintFeatures (SNS/search portion)
  geospatial.jsonl      → GeoFeatures
  ground_truth.jsonl    → case metadata + ground truth labels

Writes:
  outbreaks.jsonl       → RawCaseInput canonical schema (one JSON per line)

Merge logic per event_id:
  - Genomic: max(mutation_novelty), max(lineage_deviation), any(recombination),
             concatenated notes
  - EpiOsint: collect snippets from OSINT + SNS, aggregate anomaly/reliability,
              merge source types
  - Geo: max scores across geospatial signals
  - Sorted by case_date (chronological processing order)

Usage:
    cd Backend
    python data/combine.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent


def _load(name: str) -> list[dict]:
    path = HERE / name
    if not path.exists():
        raise FileNotFoundError(f"Missing source file: {path}")
    records = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def _group_by_event(records: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        groups[r["event_id"]].append(r)
    return dict(groups)


# ---------------------------------------------------------------------------
# Per-category merge functions
# ---------------------------------------------------------------------------

def merge_genomic(signals: list[dict]) -> dict:
    """Merge genomic feed signals into GenomicFeatures."""
    if not signals:
        return {
            "mutation_novelty": 0.0,
            "lineage_deviation": 0.0,
            "recombination_flag": False,
            "notes": "No genomic sequences available for this event",
        }
    return {
        "mutation_novelty": round(max(s["mutation_novelty"] for s in signals), 3),
        "lineage_deviation": round(max(s["lineage_deviation"] for s in signals), 3),
        "recombination_flag": any(s["recombination_flag"] for s in signals),
        "notes": "; ".join(s["notes"] for s in signals if s.get("notes")),
    }


def merge_epi_osint(osint_signals: list[dict], sns_signals: list[dict]) -> dict:
    """Merge OSINT health + SNS/search signals into EpiOsintFeatures."""
    snippets: list[str] = []
    source_types: list[str] = []

    # OSINT signals first (higher credibility)
    for sig in osint_signals:
        snippets.append(sig["snippet"])
        source_types.append(sig["source"])

    # SNS / search signals
    for sig in sns_signals:
        snippets.append(sig["snippet"])
        source_types.append(sig["source"])

    # Anomaly: max from OSINT; if none, derive from SNS sentiment
    if osint_signals:
        anomaly = max(s["anomaly_score"] for s in osint_signals)
    elif sns_signals:
        anomaly = min(1.0, max(
            s["sentiment_negative_pct"] * s["trend_velocity"] / 4.0
            for s in sns_signals
        ))
    else:
        anomaly = 0.0

    # Reliability: weighted average (OSINT = 0.7, SNS = 0.3 contribution)
    reliabilities: list[tuple[float, float]] = []  # (value, weight)
    for s in osint_signals:
        reliabilities.append((s["reliability"], 0.7))
    for s in sns_signals:
        reliabilities.append((s["reliability_hint"], 0.3))

    if reliabilities:
        total_w = sum(w for _, w in reliabilities)
        reliability = sum(v * w for v, w in reliabilities) / total_w if total_w else 0.5
    else:
        reliability = 0.5

    return {
        "news_snippets": snippets,
        "source_types": source_types,
        "anomaly_score": round(anomaly, 3),
        "reliability_hint": round(reliability, 3),
    }


def merge_geospatial(signals: list[dict]) -> dict:
    """Merge geospatial signals into GeoFeatures."""
    if not signals:
        return {
            "travel_hub_score": 0.3,
            "population_density_score": 0.3,
            "border_connectivity": 0.3,
        }
    return {
        "travel_hub_score": round(
            max(s["travel_hub_score"] for s in signals), 3),
        "population_density_score": round(
            max(s["population_density_score"] for s in signals), 3),
        "border_connectivity": round(
            max(s["border_connectivity"] for s in signals), 3),
    }


# ---------------------------------------------------------------------------
# Main combiner
# ---------------------------------------------------------------------------

def combine() -> list[dict]:
    """Read four source files + ground truth; return list of combined cases."""
    genomic_groups = _group_by_event(_load("genomic_feeds.jsonl"))
    osint_groups   = _group_by_event(_load("osint_health.jsonl"))
    sns_groups     = _group_by_event(_load("sns_search.jsonl"))
    geo_groups     = _group_by_event(_load("geospatial.jsonl"))
    gt_records     = _load("ground_truth.jsonl")

    combined: list[dict] = []

    for gt in gt_records:
        eid = gt["event_id"]

        genomic_features = merge_genomic(genomic_groups.get(eid, []))
        epi_features     = merge_epi_osint(
            osint_groups.get(eid, []),
            sns_groups.get(eid, []),
        )
        geo_features     = merge_geospatial(geo_groups.get(eid, []))

        case = {
            "case_id": eid,
            "country": gt["country"],
            "city": gt["city"],
            "lat": gt["lat"],
            "lon": gt["lon"],
            "date": gt["case_date"],
            "pathogen_label": gt["pathogen_label"],
            "genomic": genomic_features,
            "epi_osint": epi_features,
            "geo": geo_features,
            "ground_truth": {
                "true_outbreak": gt["true_outbreak"],
                "true_severity": gt["true_severity"],
                "official_alert_date": gt["official_alert_date"],
            },
        }
        combined.append(case)

    # Sort by case_date so agents process chronologically
    combined.sort(key=lambda c: c["date"])
    return combined


def write_outbreaks(cases: list[dict], path: Path | None = None) -> None:
    path = path or (HERE / "outbreaks.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        for case in cases:
            fh.write(json.dumps(case, default=str, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    cases = combine()
    write_outbreaks(cases)
    outbreaks = sum(1 for c in cases if c["ground_truth"]["true_outbreak"])
    print(f"Combined {len(cases)} cases → data/outbreaks.jsonl")
    print(f"  Outbreaks: {outbreaks}, Non-outbreaks: {len(cases) - outbreaks}")
    print(f"  Date range: {cases[0]['date']} → {cases[-1]['date']}")
    src_types = set()
    for c in cases:
        src_types.update(c["epi_osint"]["source_types"])
    print(f"  Source types in epi_osint: {sorted(src_types)}")
