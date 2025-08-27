from app.pipeline.normalizer import normalize_event

def test_normalize_event():
    evt = {"message": "Failed LOGIN for USER X", "event_type": "Auth_Failure"}
    out = normalize_event(evt)
    assert out == "failed login for user x auth_failure" or "failed login" in out
