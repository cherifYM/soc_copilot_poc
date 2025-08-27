# SOC Copilot — Deck Outline (PoC)
- Problem: noisy alerts, analyst fatigue
- Solution: normalize + redact + cluster + summarize + gated actions
- KPIs: >=40% suppression, <5% false-dismissals, MTTA -30%, 100% audited decisions
- Architecture: FastAPI + SQLAlchemy + Streamlit
- PoC Constraints: No auto-remediation, approval gate only, PDPL tag SA/AE
