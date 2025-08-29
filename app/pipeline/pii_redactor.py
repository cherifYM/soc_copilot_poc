
import re
from typing import Tuple
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
PHONE_RE = re.compile(r"\b(?:\+?\d{1,2}[ -]?)?(?:\(\d{3}\)|\d{3})[ -]?\d{3}[ -]?\d{4}\b")
def redact_pii(text: str) -> Tuple[str, int]:
    count = 0
    def sub_and_count(pattern, repl, s):
        nonlocal count
        s2, n = pattern.subn(repl, s); count += n; return s2
    red = text
    red = sub_and_count(EMAIL_RE, "[REDACTED:EMAIL]", red)
    red = sub_and_count(IPV4_RE, "[REDACTED:IP]", red)
    red = sub_and_count(PHONE_RE, "[REDACTED:PHONE]", red)
    return red, count
def residency_tag(evt: dict, default_tag: str = "SA") -> str:
    region = (evt.get("region") or evt.get("country") or "").strip().lower()
    if region in {"sa", "saudi", "saudi arabia", "ksa"}: return "SA"
    if region in {"ae", "uae", "united arab emirates", "dubai", "abudhabi", "abu dhabi"}: return "AE"
    return default_tag


# Back-compat: some modules expect this name
REDACTION_PATTERNS = {
    "EMAIL": EMAIL_RE,
    "IP": IPV4_RE,
    "PHONE": PHONE_RE,
}
