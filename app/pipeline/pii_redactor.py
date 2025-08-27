# app/pipeline/pii_redactor.py
import re
from typing import Tuple
from collections import defaultdict

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
IPV4_RE  = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
PHONE_RE = re.compile(r"\b(?:\+?\d{1,2}[ -]?)?(?:\(\d{3}\)|\d{3})[ -]?\d{3}[ -]?\d{4}\b")
CARD_RE  = re.compile(r"\b(?:\d[ -]*?){13,16}\b")

# Export patterns for reuse (e.g., evidence aggregation)
REDACTION_PATTERNS = {
    "EMAIL": EMAIL_RE,
    "IP": IPV4_RE,
    "PHONE": PHONE_RE,
    "CARD": CARD_RE,
}

def _apply(pattern: re.Pattern, label: str, s: str, counts: dict) -> str:
    def _repl(_m):
        counts[label] = counts.get(label, 0) + 1
        return f"[REDACTED:{label}]"
    return pattern.sub(_repl, s)

def redact_pii(text: str) -> Tuple[str, int]:
    """Redact basic PII (email, IPv4, phone, card). Returns (redacted_text, total_redactions)."""
    counts: dict = {}
    out = text or ""
    out = _apply(EMAIL_RE, "EMAIL", out, counts)
    out = _apply(IPV4_RE, "IP", out, counts)
    out = _apply(PHONE_RE, "PHONE", out, counts)
    out = _apply(CARD_RE, "CARD", out, counts)
    total = sum(counts.values())
    return out, total

def residency_tag(evt: dict, default_tag: str = "SA") -> str:
    region = (evt.get("region") or evt.get("country") or "").strip().lower()
    if region in {"sa", "saudi", "saudi arabia", "ksa"}:
        return "SA"
    if region in {"ae", "uae", "united arab emirates", "dubai", "abudhabi", "abu dhabi"}:
        return "AE"
    return default_tag
