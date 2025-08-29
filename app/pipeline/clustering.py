
import hashlib
def cluster_key(evt: dict, normalized: str) -> str:
    source = (evt.get("source") or "unknown").lower()
    et = (evt.get("event_type") or evt.get("action") or "event").lower()
    basis = f"{source}|{et}|{normalized}".encode("utf-8")
    return hashlib.sha1(basis).hexdigest()[:16]
def incident_title(evt: dict) -> str:
    source = evt.get("source", "unknown")
    et = evt.get("event_type") or evt.get("action") or "event"
    return f"{source} - {et}"


def explain_cluster(evt: dict, normalized: str) -> str:
    """Human-readable reason for the cluster key (stub for PoC)."""
    source = (evt.get("source") or "unknown").lower()
    et = (evt.get("event_type") or evt.get("action") or "event").lower()
    return f"clustered by {source}/{et} + normalized pattern"
