# SOC Copilot PoC (PDPL-first, explainable suppression)

**Goal:** Ingest noisy logs → **normalize → PII redaction + residency tag (SA/AE) → cluster (reduce noise) → deterministic summary → guardrailed playbooks** → human approval + audit → metrics.

**Pilot KPIs:** ≥ **40% suppression** with **<5% false-dismissals**, **MTTA ↓ ~30%**, **100% audited decisions**.

## Features
- **PDPL-first** redaction on ingest; **residency tags** (SA/AE) stored end-to-end.
- **Clustering** with time-bucket + user/IP → high suppression, *explainable*.
- **Benign → noise** with **promotion safety net** (≥5 failures then a success ⇒ `open`).
- **Evidence API**: redaction counts, why-clustered, approvals trail.
- **Metrics**: suppression, active suppression, dup rate.

## Quickstart
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
make run-api               # http://localhost:8000
make seed                  # seed synthetic events
make run-ui                # http://localhost:8501
=======
# SOC Copilot (PoC)

Pipeline: ingest logs → normalize → PII redaction + residency tag (SA/AE) → cluster → deterministic summary → suggest guardrailed actions → human approval + audit → metrics.

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Terminal A
make run-api  # http://localhost:8000

# Seed some noisy events (in another terminal while API is running)
make seed

# Terminal B
make run-ui   # http://localhost:8501
```
>>>>>>> 01defdf (Initial code import (local state))
