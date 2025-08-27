# tests/test_benign_noise.py
from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)

def test_benign_is_noise_incident():
    payload = {"events": [
        {"source":"app","event_type":"auth_success","message":"login for user a@x.com from 1.2.3.4","ts":"2025-08-22T10:00:00Z"}
    ]}
    r = client.post("/ingest/logs", json=payload)
    assert r.status_code == 200
    incs = client.get("/incidents").json()
    assert any(i["status"] in {"noise","open"} for i in incs)  # sanity
