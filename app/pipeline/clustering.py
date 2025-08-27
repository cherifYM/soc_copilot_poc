# app/pipeline/clustering.py
from hashlib import blake2b
from datetime import datetime, timezone, timedelta
import os, re

# Allow tuning via env: 900s = 15 minutes
_BUCKET_SECONDS = int(os.getenv("CLUSTER_BUCKET_SECONDS", "900"))

def _safe(s): 
    return (s or "").strip().lower()

def _extract_user(norm_msg: str) -> str:
    # works on our normalized text e.g., "successful login for user [redacted:email] from [redacted:ip]"
    m = re.search(r"user\s+([^\s\]]+)", norm_msg, flags=re.I)
    return (m.group(1) or "").lower() if m else ""

def _extract_ip(norm_msg: str) -> str:
    # prefers explicit IP; falls back to the token that appears after 'from'
    m = re.search(r"\b(\d{1,3}(?:\.\d{1,3}){3})\b", norm_msg)
    if m: 
        return m.group(1)
    m2 = re.search(r"from\s+([^\s\]]+)", norm_msg, flags=re.I)
    return (m2.group(1) or "").lower() if m2 else ""

def _to_bucket(ts: str | None, bucket_seconds: int = _BUCKET_SECONDS) -> tuple[str, tuple[int,int]]:
    """
    Returns (bucket_key, (start_epoch, end_epoch))
    - ts: ISO 8601 like "2025-08-22T10:00:05Z"; if None, uses now().
    """
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00")) if ts else datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    except Exception:
        dt = datetime.now(timezone.utc)
    start = int(dt.timestamp()) // bucket_seconds * bucket_seconds
    end = start + bucket_seconds - 1
    return str(start // bucket_seconds), (start, end)

def cluster_key(evt: dict, norm_cluster: str, bucket_seconds: int = _BUCKET_SECONDS) -> str:
    user = _safe(evt.get("user")) or _extract_user(norm_cluster)
    ip   = _safe(evt.get("ip"))   or _extract_ip(norm_cluster)
    et   = _safe(evt.get("event_type"))
    bkt, _ = _to_bucket(evt.get("ts"), bucket_seconds)

    # minimal, stable token set
    material = "|".join([et, user, ip, bkt])
    return blake2b(material.encode("utf-8"), digest_size=8).hexdigest()

def incident_title(evt: dict) -> str:
    et = _safe(evt.get("event_type"))
    user = _safe(evt.get("user"))
    return f"{et or 'event'} cluster for {user or 'unknown'}"

def explain_cluster(evt: dict, norm_cluster: str, bucket_seconds: int = _BUCKET_SECONDS) -> dict:
    """Return features used for clustering (for UI/explainability)."""
    user = _safe(evt.get("user")) or _extract_user(norm_cluster)
    ip   = _safe(evt.get("ip"))   or _extract_ip(norm_cluster)
    et   = _safe(evt.get("event_type"))
    bkt_key, (start_epoch, end_epoch) = _to_bucket(evt.get("ts"), bucket_seconds)
    window = {
        "bucket_seconds": bucket_seconds,
        "bucket_index": bkt_key,
        "window_start_iso": datetime.fromtimestamp(start_epoch, tz=timezone.utc).isoformat(),
        "window_end_iso": datetime.fromtimestamp(end_epoch, tz=timezone.utc).isoformat(),
    }
    tokens = {"event_type": et, "user": user, "ip": ip, "time_bucket": bkt_key}
    return {"tokens": tokens, "window": window}