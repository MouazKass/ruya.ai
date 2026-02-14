# SENTINEL Backend

AI-powered early-warning system for pandemic and outbreak detection.
Built for the Ministry of Health dashboard — processes synthetic outbreak cases through a four-agent pipeline, fuses signals with self-improving weights, and gates all external dispatch behind human approval.

## Architecture

```
Input Sources
┌──────────────────────────────────────────────────────────────────────┐
│  Geospatial Data       SNS & Search         Official OSINT Health   │
│  OSM, Flights,         Social Media,        Signals: WHO DON,       │
│  Pop Density           Forums, Google       ProMED, News APIs       │
│                        Search / Trends                              │
│                        Metadata             Genomic Feeds            │
│                                             GISAID, NCBI GenBank    │
└──────────────────────────────────────────────────────────────────────┘
          │                    │                    │
          ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Agent Pipeline (sequential)                  │
│  1. Ingest + Normalize + Credibility                            │
│  2. Genomics Risk Analyst                                       │
│  3. Epi/OSINT Signal Analyst                                    │
│  4. Meta-Agent + Self-Improvement Controller                    │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────┐     ┌────────────────────────┐
│  Guardrail Filter   │────▶│  Approval Queue        │
│  severity >= 7      │     │  (MoH Dashboard)       │
│  confidence >= 60%  │     └────────────────────────┘
└─────────────────────┘              │
                                     ▼
                          ┌────────────────────────┐
                          │  Dispatch (dry-run)     │
                          │  ElevenLabs Voice Stub  │
                          │  Email Stub             │
                          └────────────────────────┘
```

### RAG: Three-source retrieval

1. **ClickHouse vector index** — normalized case records with embeddings
2. **Past outbreak index** — synthetic dataset loaded at startup
3. **Strategy memory index** — learned heuristics and prompt updates

### Self-improvement loop

After each case the system:
- Compares prediction to ground truth
- Updates fusion weights (`w_genomics`, `w_epi`, `w_geo`) via gradient-style rule
- Adjusts decision threshold to reduce false alarms
- Writes strategy notes back into ClickHouse → embedded → fed to RAG on next run

---

## Quick start

### Docker Compose (recommended)

```bash
cd Backend

# Create .env from example (edit to taste)
cp .env.example .env

# Build and start ClickHouse + backend
docker compose up --build
```

Backend is accessible at **http://localhost:8000**.
OpenAPI docs at **http://localhost:8000/docs**.

### Local development (no Docker)

Prerequisites: Python 3.11+, a running ClickHouse instance on `localhost:8123`.

```bash
cd Backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS

pip install -r requirements.txt

# Point at local ClickHouse
set CLICKHOUSE_HOST=localhost  # Windows
# export CLICKHOUSE_HOST=localhost  # Linux/macOS

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Running tests

```bash
cd Backend
pip install -r requirements.txt
pytest tests/ -v
```

---

## API reference

All endpoints are prefixed with `/api`. Full OpenAPI spec at `/docs`.

### Dashboard

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/dashboard` | Aggregated dashboard state: recent cases, metrics, pending approvals, per-case summaries |

### Runs

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/run/start` | Start a simulation run over N synthetic cases |
| `GET` | `/api/run/{run_id}/status` | Poll run progress |

### Cases

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/case/{case_id}` | Full case detail: RAG context, agent outputs, decision, approvals, audit trail |

### Approvals

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/approval/{case_id}` | Approve / reject / request more evidence |

### Health

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness check |

---

## Sample curl commands

### Start a simulation run (5 cases)

```bash
curl -X POST http://localhost:8000/api/run/start \
  -H "Content-Type: application/json" \
  -d '{"num_cases": 5}'
```

Response:
```json
{"run_id": "abc12345-...", "status": "running"}
```

### Check run status

```bash
curl http://localhost:8000/api/run/{run_id}/status
```

### Get dashboard state

```bash
curl http://localhost:8000/api/dashboard
```

### Get full case details

```bash
curl http://localhost:8000/api/case/CASE-002
```

### Approve a case for dispatch

```bash
curl -X POST http://localhost:8000/api/approval/CASE-002 \
  -H "Content-Type: application/json" \
  -d '{"decision": "approve", "reviewer_name": "Dr. Amara", "notes": "Confirmed by field team"}'
```

### Reject a case

```bash
curl -X POST http://localhost:8000/api/approval/CASE-001 \
  -H "Content-Type: application/json" \
  -d '{"decision": "reject", "notes": "False alarm - seasonal pattern"}'
```

### Request more evidence

```bash
curl -X POST http://localhost:8000/api/approval/CASE-003 \
  -H "Content-Type: application/json" \
  -d '{"decision": "request_more_evidence", "notes": "Need lab confirmation before escalation"}'
```

---

## Project structure

```
Backend/
├── app/
│   ├── main.py              # FastAPI bootstrap, middleware, lifecycle
│   ├── config.py            # Pydantic settings (env-driven)
│   ├── models.py            # Strict Pydantic schemas for all data
│   ├── service.py           # Core orchestration (run pipeline, approvals, dashboard)
│   ├── api/
│   │   ├── dashboard.py     # GET /api/dashboard
│   │   ├── runs.py          # POST /api/run/start, GET /api/run/{id}/status
│   │   ├── cases.py         # GET /api/case/{id}
│   │   └── approvals.py     # POST /api/approval/{id}
│   ├── agents/
│   │   ├── base.py          # Bedrock LLM client + retry/repair + local fallback
│   │   ├── ingest.py        # Agent 1: Ingest + Normalize + Credibility
│   │   ├── genomics.py      # Agent 2: Genomics Risk Analyst
│   │   ├── epi_osint.py     # Agent 3: Epi/OSINT Signal Analyst
│   │   ├── meta.py          # Agent 4: Meta-Agent + Self-Improvement Controller
│   │   └── prompts/         # Per-agent prompt templates
│   ├── rag/
│   │   ├── embed.py         # Bedrock embeddings + deterministic local fallback
│   │   ├── index.py         # In-memory vector index (cosine similarity)
│   │   ├── retrieve.py      # Three-source retrieval orchestrator
│   │   └── rerank.py        # Pluggable rerank step
│   ├── improve/
│   │   ├── evaluate.py      # Run metrics (lead time, FAR, MAE, Brier)
│   │   └── update.py        # Fusion weight update + strategy note builder
│   ├── storage/
│   │   ├── clickhouse.py    # ClickHouse client wrapper (safe queries)
│   │   ├── schema.py        # DDL migrations (8 tables)
│   │   └── audit.py         # Audit event logger
│   └── dispatch/
│       ├── base.py          # Dispatch manager (approval-gated)
│       ├── elevenlabs_stub.py
│       └── email_stub.py
├── data/
│   └── outbreaks.jsonl      # 24 synthetic cases with ground truth
├── tests/
│   ├── conftest.py
│   ├── test_schema_validation.py
│   ├── test_weight_update.py
│   └── test_approval_gating.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## ClickHouse tables

| Table | Purpose |
|-------|---------|
| `cases` | Normalized case records, ground truth, embeddings |
| `agent_outputs` | Per-case per-agent JSON output + score + confidence |
| `decisions` | Fused score, severity, confidence, rationale, contributions |
| `approvals` | Status (pending/approved/rejected/request_more_evidence), reviewer, dispatch log |
| `runs` | Run ID, start/end, config snapshot, progress |
| `strategy_memory` | Strategy notes, updated prompts, fusion weights, embeddings |
| `audit_logs` | Every action logged with actor + payload |
| `metrics` | Per-run: lead_time_days, false_alarm_rate, severity_mae, brier_score |

## Environment variables

See [.env.example](.env.example) for all available settings.

Key flags:
- `USE_BEDROCK=false` — agents use deterministic local fallbacks (no AWS needed for demo)
- `USE_BEDROCK_EMBEDDINGS=false` — embeddings use local hash-based method
- `DISPATCH_DRY_RUN=true` — dispatch stubs log but don't call real providers

## Input sources

The system is designed to ingest signals from four input source categories:

- **Geospatial Data** — OSM, Flights, Population Density
- **SNS and Search** — Social Media, Forums, Google Search / Trends Metadata
- **Official OSINT Health Signals** — WHO DON, ProMED, News APIs
- **Genomic Feeds** — GISAID, NCBI GenBank

For the hackathon demo, all signals are pre-baked into the synthetic `outbreaks.jsonl` dataset. The architecture supports plugging in live adapters for each source category.
