.PHONY: run-api run-ui seed test lint

run-api:
	uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000

run-ui:
	streamlit run ui/streamlit_app.py --server.port 8501

seed:
	python scripts/seed_data.py

test:
	pytest -q
