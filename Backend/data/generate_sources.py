"""Decompose combined outbreaks.jsonl into 4 time-series source files.

Reads the canonical outbreaks.jsonl and produces:
  genomic_feeds.jsonl     – GISAID / NCBI GenBank sequence data
  osint_health.jsonl      – WHO DON / ProMED / News API / WHO Bulletin / Hospital reports
  sns_search.jsonl        – Social media / Forums / Google Trends / Local press
  geospatial.jsonl        – Flight data / OSM / Population density context
  ground_truth.jsonl      – Event-level ground truth labels

All timestamps are placed within Jan – Feb 2026.
Agents only see the present and past.

Usage:
    cd Backend
    python data/generate_sources.py
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).parent

# ---------------------------------------------------------------------------
# Date compression – map existing 2025 dates to Jan 3 – Feb 5, 2026
# ---------------------------------------------------------------------------
OLD_START = date(2025, 1, 11)
OLD_END = date(2025, 7, 4)
NEW_START = date(2026, 1, 3)
NEW_END = date(2026, 2, 5)


def _compress_date(d: str | date) -> date:
    if isinstance(d, str):
        d = date.fromisoformat(d)
    old_span = max((OLD_END - OLD_START).days, 1)
    new_span = (NEW_END - NEW_START).days
    offset = max(0, (d - OLD_START).days)
    new_offset = min(round(offset * new_span / old_span), new_span)
    return NEW_START + timedelta(days=new_offset)


# ---------------------------------------------------------------------------
# Source-category routing
# ---------------------------------------------------------------------------
OSINT_SOURCES = {"who_don", "promed", "news_api", "who_bulletin", "hospital_report"}
SNS_SOURCES = {"social_media", "forum", "google_trends", "local_press"}
GEO_SOURCES = {"osm_geospatial", "flight_data"}
GENOMIC_ALERT_SOURCES = {"gisaid", "ncbi_genbank"}

# ---------------------------------------------------------------------------
# Timestamp offsets (days-before-case_date, hour, minute)
# Ordered from earliest to latest detection in a typical outbreak signal:
#   SNS → genomic → OSINT official → geospatial context
# ---------------------------------------------------------------------------
TS_OFFSETS: dict[str, tuple[int, int, int]] = {
    "social_media":    (-6, 21, 30),
    "forum":           (-5, 14, 15),
    "google_trends":   (-5,  0,  0),
    "local_press":     (-3, 11,  0),
    "gisaid":          (-4, 10, 30),
    "ncbi_genbank":    (-3, 16, 45),
    "promed":          (-3,  8, 20),
    "news_api":        (-2, 14,  0),
    "who_don":         (-2,  7,  0),
    "who_bulletin":    (-2,  9, 30),
    "hospital_report": (-1,  6,  0),
    "osm_geospatial":  (-2,  4,  0),
    "flight_data":     (-1,  5,  0),
    "pop_density":     (-1,  4, 30),
}


def _make_ts(case_date: date, source: str, seq: int = 0) -> str:
    """ISO-8601 timestamp for a signal, offset from case_date by source type."""
    day_off, h, m = TS_OFFSETS.get(source, (-2, 12, 0))
    dt = datetime(case_date.year, case_date.month, case_date.day,
                  h, m, 0, tzinfo=timezone.utc) + timedelta(days=day_off)
    dt += timedelta(minutes=seq * 47)          # stagger duplicates
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Text extraction helpers
# ---------------------------------------------------------------------------
def _headline(snippet: str) -> str:
    first = snippet.split(". ")[0]
    return first if len(first) <= 120 else first[:117] + "..."


def _case_count(snippet: str) -> int | None:
    for pat in (r"(\d+)\s+(?:confirmed|suspected|human|total)\s+case",
                r"reports?\s+(\d+)\s+case", r"(\d+)\s+(?:case|people|patients)"):
        m = re.search(pat, snippet, re.I)
        if m:
            return int(m.group(1))
    return None


def _keyword(snippet: str, pathogen: str | None) -> str:
    for pat in (r"'([^']{3,60})'", r'"([^"]{3,60})"'):
        m = re.search(pat, snippet)
        if m:
            return m.group(1)
    if pathogen:
        return pathogen.split("/")[0].split(" ")[0].lower() + " outbreak"
    return "mystery illness"


def _mention_count(snippet: str, anomaly: float) -> int:
    m = re.search(r"(\d+)%", snippet)
    if m:
        return int(float(m.group(1)) * 8)
    m = re.search(r"(\d+)k\s+upvote", snippet, re.I)
    if m:
        return int(m.group(1)) * 1000
    return max(30, int(anomaly * 700))


def _genomic_source(notes: str) -> str:
    lo = notes.lower()
    has_gisaid = "gisaid" in lo
    has_ncbi = "ncbi" in lo or "genbank" in lo
    if has_gisaid and has_ncbi:
        return "both"
    if has_ncbi:
        return "ncbi_genbank"
    return "gisaid"


def _lineage(text: str) -> str | None:
    for pat in (r"lineage\s+([A-Za-z0-9._/-]+)",
                r"clade\s+([A-Za-z0-9._/-]+)",
                r"genotype\s+([A-Za-z0-9._/-]+)",
                r"subclade\s+([A-Za-z0-9._/-]+)"):
        m = re.search(pat, text, re.I)
        if m:
            return m.group(1)
    return None


def _seq_count(text: str) -> int:
    for pat in (r"(\d+)\s+(?:sequences?|genomes?|isolates?)",):
        m = re.search(pat, text, re.I)
        if m:
            v = int(m.group(1))
            if v < 50000:
                return v
    return 1


# ---------------------------------------------------------------------------
# Main decomposition
# ---------------------------------------------------------------------------
def generate() -> None:
    cases: list[dict] = []
    with open(HERE / "outbreaks.jsonl", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                cases.append(json.loads(line))

    gen_out: list[dict] = []
    osi_out: list[dict] = []
    sns_out: list[dict] = []
    geo_out: list[dict] = []
    gt_out:  list[dict] = []

    gid = oid = sid = lid = 0

    for case in cases:
        cid      = case["case_id"]
        old_d    = case["date"]
        new_d    = _compress_date(old_d)
        co, ci   = case["country"], case["city"]
        la, lo   = case["lat"], case["lon"]
        pa       = case.get("pathogen_label")
        gen      = case["genomic"]
        epi      = case["epi_osint"]
        geo      = case["geo"]
        gt       = case["ground_truth"]

        # ---- ground truth ------------------------------------------------
        new_alert = _compress_date(gt["official_alert_date"])
        if new_alert <= new_d:
            new_alert = new_d + timedelta(days=3)
        gt_out.append({
            "event_id": cid, "country": co, "city": ci, "lat": la, "lon": lo,
            "case_date": new_d.isoformat(), "pathogen_label": pa,
            "true_outbreak": gt["true_outbreak"],
            "true_severity": gt["true_severity"],
            "official_alert_date": new_alert.isoformat(),
        })

        # ---- genomic feeds -----------------------------------------------
        src = _genomic_source(gen["notes"])
        srcs = ["gisaid", "ncbi_genbank"] if src == "both" else [src]
        for gs in srcs:
            gid += 1
            gen_out.append({
                "signal_id": f"GEN-{gid:03d}",
                "event_id": cid, "source": gs,
                "timestamp": _make_ts(new_d, gs),
                "country": co, "city": ci, "lat": la, "lon": lo,
                "pathogen": pa,
                "lineage": _lineage(gen["notes"]),
                "mutation_novelty": gen["mutation_novelty"],
                "lineage_deviation": gen["lineage_deviation"],
                "recombination_flag": gen["recombination_flag"],
                "sequence_count": _seq_count(gen["notes"]),
                "notes": gen["notes"],
            })

        # ---- route epi_osint snippets ------------------------------------
        src_types = epi.get("source_types", [])
        snippets  = epi.get("news_snippets", [])
        oseq = sseq = gseq = 0

        for i, (st, snip) in enumerate(zip(src_types, snippets)):
            if st in OSINT_SOURCES:
                oid += 1
                osi_out.append({
                    "signal_id": f"OSINT-{oid:03d}",
                    "event_id": cid, "source": st,
                    "timestamp": _make_ts(new_d, st, oseq),
                    "country": co, "city": ci, "lat": la, "lon": lo,
                    "pathogen_mention": pa,
                    "headline": _headline(snip),
                    "snippet": snip,
                    "anomaly_score": round(epi["anomaly_score"], 3),
                    "reliability": round(
                        min(1.0, epi["reliability_hint"]
                            + (0.15 if st in {"who_don","hospital_report"} else 0.0)),
                        3),
                    "case_count_mentioned": _case_count(snip),
                })
                oseq += 1

            elif st in SNS_SOURCES:
                sid += 1
                an = epi["anomaly_score"]
                rel = epi["reliability_hint"]
                sns_out.append({
                    "signal_id": f"SNS-{sid:03d}",
                    "event_id": cid, "source": st,
                    "timestamp": _make_ts(new_d, st, sseq),
                    "country": co, "city": ci, "lat": la, "lon": lo,
                    "keyword": _keyword(snip, pa),
                    "mention_count": _mention_count(snip, an),
                    "sentiment_negative_pct": round(min(1.0, an * 0.85), 3),
                    "trend_velocity": round(max(0.5, an * 3.5), 2),
                    "snippet": snip,
                    "reliability_hint": round(
                        max(0.01, rel * (0.65 if st == "social_media" else 0.80)),
                        3),
                })
                sseq += 1

            elif st in GEO_SOURCES:
                lid += 1
                geo_out.append({
                    "signal_id": f"GEO-{lid:03d}",
                    "event_id": cid, "source": st,
                    "timestamp": _make_ts(new_d, st, gseq),
                    "country": co, "city": ci, "lat": la, "lon": lo,
                    "travel_hub_score": geo["travel_hub_score"],
                    "population_density_score": geo["population_density_score"],
                    "border_connectivity": geo["border_connectivity"],
                    "notes": snip,
                })
                gseq += 1

            elif st in GENOMIC_ALERT_SOURCES:
                # Genomic alert embedded in epi_osint source list
                gid += 1
                gen_out.append({
                    "signal_id": f"GEN-{gid:03d}",
                    "event_id": cid, "source": st,
                    "timestamp": _make_ts(new_d, st, 1),
                    "country": co, "city": ci, "lat": la, "lon": lo,
                    "pathogen": pa,
                    "lineage": _lineage(snip) or _lineage(gen["notes"]),
                    "mutation_novelty": gen["mutation_novelty"],
                    "lineage_deviation": gen["lineage_deviation"],
                    "recombination_flag": gen["recombination_flag"],
                    "sequence_count": _seq_count(snip),
                    "notes": snip,
                })

        # ---- default geospatial if none came from snippets ---------------
        has_geo_from_snippets = any(s in GEO_SOURCES for s in src_types)
        if not has_geo_from_snippets:
            lid += 1
            geo_src = ("pop_density"
                       if geo["population_density_score"] > geo["travel_hub_score"]
                       else "flight_data")
            geo_out.append({
                "signal_id": f"GEO-{lid:03d}",
                "event_id": cid, "source": geo_src,
                "timestamp": _make_ts(new_d, geo_src),
                "country": co, "city": ci, "lat": la, "lon": lo,
                "travel_hub_score": geo["travel_hub_score"],
                "population_density_score": geo["population_density_score"],
                "border_connectivity": geo["border_connectivity"],
                "notes": (f"Geospatial context for {ci}, {co}: travel-hub "
                          f"{geo['travel_hub_score']}, pop-density "
                          f"{geo['population_density_score']}, border "
                          f"{geo['border_connectivity']}"),
            })

    # ---- write JSONL files (sorted chronologically) ----------------------
    _write(HERE / "genomic_feeds.jsonl", sorted(gen_out,  key=lambda s: s["timestamp"]))
    _write(HERE / "osint_health.jsonl",  sorted(osi_out,  key=lambda s: s["timestamp"]))
    _write(HERE / "sns_search.jsonl",    sorted(sns_out,  key=lambda s: s["timestamp"]))
    _write(HERE / "geospatial.jsonl",    sorted(geo_out,  key=lambda s: s["timestamp"]))
    _write(HERE / "ground_truth.jsonl",  gt_out)

    print("Generated source files:")
    print(f"  genomic_feeds.jsonl : {len(gen_out):3d} signals")
    print(f"  osint_health.jsonl  : {len(osi_out):3d} signals")
    print(f"  sns_search.jsonl    : {len(sns_out):3d} signals")
    print(f"  geospatial.jsonl    : {len(geo_out):3d} signals")
    print(f"  ground_truth.jsonl  : {len(gt_out):3d} events")


def _write(path: Path, rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, default=str, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    generate()
