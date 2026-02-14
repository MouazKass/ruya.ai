<h1 align="center"> SENTINEL - Self-Improving Pandemic Early Warning System </h1>

SENTINEL is a multi-agent early warning system that detects emerging outbreak signals by fusing genomic, epidemiological/OSINT, and geospatial indicators. It improves over time by evaluating each run against ground truth, updating fusion weights, and refining agent strategies. Alerts are never dispatched without explicit human approval through a Ministry of Health (MoH) dashboard.

WHAT IT DOES
- Ingests and normalizes outbreak-related signals from multiple sources into a canonical schema.
- Stores everything in ClickHouse for analytics, audit, and repeatable simulation runs.
- Retrieves relevant prior cases and learned heuristics using RAG, so agents start with “memory”.
- Runs three specialist agents sequentially:
  1) Genomic Analyst: mutation novelty and risk indicators
  2) Epi/OSINT Analyst: source reliability and signal vs noise
  3) Geo Modeler: spread corridors and urgency estimates
- Uses a Meta-Agent to fuse agent outputs into a single threat score with a clear rationale.
- Applies guardrails (severity and confidence thresholds) to filter low-quality outputs.
- Posts eligible alerts to the MoH dashboard for review.
- Requires human approval before any external dispatch (voice/email).
- Logs every step to ClickHouse for an audit trail and dashboard analytics.

WHY THIS IS “SELF-IMPROVING”
The system closes the loop after every run:
1) Predict: agents + meta-agent produce a threat assessment.
2) Evaluate: compare to ground truth (historical labels or simulation truth).
3) Learn: update fusion weights and refine prompts/heuristics.
4) Remember: store updated strategy memory and embed it into a vector index.
5) Retrieve: next run pulls these learned heuristics via RAG before agents begin.
The “strategy memory → RAG” feedback path is the self-improvement mechanism.

KEY GUARANTEES
- No external actions without human approval: dispatch is gated by the MoH dashboard.
- Explainable decisions: threat score includes agent contributions and rationale.
- Auditable: all inputs, outputs, and decisions are stored in ClickHouse.

SYSTEM ARCHITECTURE
1) Input Sources → Ingest & Normalize → ClickHouse
2) RAG Retrieval (cases + ClickHouse index + strategy memory) → Agents
3) Meta-Agent → Guardrail → MoH Dashboard → Human Approval → Dispatch
4) Evaluation + updates → Strategy Memory → back into RAG for the next run

<div align="center">
<img width="497" height="1115" alt="image" src="https://github.com/user-attachments/assets/3e489f6a-35cd-433d-99c7-b4d0f1699893" />
</div>

METRICS (MEASURABLE IMPROVEMENT)
Tracked per run and shown on the dashboard:
- Detection lead time: days earlier than the official alert date
- False alarm rate: alerts raised on non-outbreak cases
- Severity accuracy: error vs ground truth severity
Optional:
- Calibration: confidence vs outcome alignment

HUMAN APPROVAL WORKFLOW
1) System posts assessment + evidence to the MoH dashboard.
2) Reviewer chooses:
   - Approve: triggers dispatch
   - Reject: no external actions occur
   - Request more evidence: system re-runs retrieval and expands evidence

GUARDRAILS
Default thresholds:
- Severity ≥ 7 (on a 1–10 scale)
- Confidence ≥ 60%
Guardrails only decide if a case is eligible for review. Dispatch still requires human approval.

TECH STACK
- Backend: FastAPI
- Agents: LLM-powered specialist agents + meta-agent orchestrator
- Storage + analytics: ClickHouse
- Retrieval: vector index over cases + ClickHouse records + strategy memory
- Dashboard: React
- Dispatch: ElevenLabs (voice), verification email


