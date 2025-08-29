PYTHON := ./.venv/bin/python
STREAMLIT := ./.venv/bin/streamlit

.PHONY: bootstrap run-api run-ui seed test

bootstrap:
	python3 -m venv .venv && ./.venv/bin/python -m pip install --upgrade pip && ./.venv/bin/pip install -r requirements.txt && cp -n .env.example .env || true

run-api:
	PYTHONPATH=. $(PYTHON) -m uvicorn app.api.main:app --reload --reload-dir . --host 0.0.0.0 --port 8000

run-ui:
	API_BASE=http://localhost:8000 $(STREAMLIT) run ui/streamlit_app.py --server.port 8501

seed:
	$(PYTHON) scripts/seed_data.py

test:
	./.venv/bin/pytest -q
