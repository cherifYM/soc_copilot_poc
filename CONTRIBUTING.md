# Contributing

## Quickstart
1. `python3 -m venv .venv && source .venv/bin/activate`
2. `pip install -r requirements.txt`
3. Terminal A: `make run-api` (http://localhost:8000)
4. Terminal B: `make seed` then `make run-ui` (http://localhost:8501)

## Tests
- `pytest -q`
- Please add a smoke test for new pipeline behavior (no PII in tests).

## Code style
- Python 3.10+, FastAPI, SQLAlchemy 2.x.
- Deterministic summaries by default; keep actions **human-gated**.
- No raw PII in examples, logs, or tests.

## Licensing
By contributing, you agree your contributions are licensed under **AGPL-3.0**.
