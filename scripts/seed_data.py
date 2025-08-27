# scripts/seed_data.py
import os, sys, time
import requests
from requests.exceptions import RequestException

API = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")

def wait_for_health(url: str, max_wait: float = 15.0) -> bool:
    deadline = time.time() + max_wait
    delay = 0.5
    while time.time() < deadline:
        try:
            res = requests.get(f"{url}/health", timeout=1.5)
            if res.ok:
                return True
        except Exception:
            pass
        time.sleep(delay)
        delay = min(2.5, delay * 1.5)
    return False

def build_payload():
    # Keep the shape compatible with your API; swap in your real generator if needed.
    return {
        "source": "seed",
        "events": [
            {"message": "Successful login for user alice@example.com from 203.0.113.10", "ts": "2025-08-22T10:00:00Z"},
            {"message": "Failed login for user bob@example.com from 198.51.100.23", "ts": "2025-08-22T10:00:05Z"},
        ],
    }

def main():
    if not wait_for_health(API):
        sys.stderr.write(f"[seed] API not reachable at {API}. Start the API first.\n")
        sys.exit(2)
    payload = build_payload()
    try:
        r = requests.post(f"{API}/ingest/logs", json=payload, timeout=10)
        print(r.status_code, r.text)
        r.raise_for_status()
    except RequestException as e:
        sys.stderr.write(f"[seed] Request failed: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
