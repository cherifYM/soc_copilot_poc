# tests/test_clustering_bucket.py
from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)

def test_time_bucket_splits_clusters():
    # Same user/IP/type but 20 minutes apart → should become different clusters when bucket=15m
    evs = [
        {"source":"app","event_type":"auth_failure","message":"Failed login for user a@x.com from 1.2.3.4","ts":"2025-08-25T10:00:00Z"},
        {"source":"app","event_type":"auth_failure","message":"Failed login for user a@x.com from 1.2.3.4","ts":"2025-08-25T10:20:00Z"},
    ]
    r = client.post("/ingest/logs", json={"events": evs})
    assert r.status_code == 200

    # Pull recent incidents and ensure at least 2 separate incidents present among latest few
    incs = client.get("/incidents").json()
    assert len(incs) >= 2
