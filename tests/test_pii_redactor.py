from app.pipeline.pii_redactor import redact_pii

def test_redact_email_ip_phone():
    text = "User john.doe@example.com from 192.168.1.1 called +1 (416) 555-1212"
    red, n = redact_pii(text)
    assert "example.com" not in red
    assert "192.168.1.1" not in red
    assert "416" not in red
    assert n >= 3
