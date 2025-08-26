# Changelog

## v0.2.0 (planned)
- Optional **AI summaries** (flagged): redacted-only context; PDPL-safe.
- Env: `USE_LLM_SUMMARY`, `OPENAI_API_KEY`, `OPENAI_MODEL` (defaults provided).

## v0.1.0
- PDPL redaction + residency tags (SA/AE).
- Explainable clustering (user/IP + time bucket), **benign→noise**.
- **Promotion safety net** (≥5 failures then success ⇒ `open`).
- Evidence endpoints (redaction counts, **why-clustered**, approvals).
- Metrics: suppression, active suppression, dup rate.
- Joined-load fix for `/events/recent` (no N+1).
