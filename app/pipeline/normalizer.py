import re
from typing import Dict

def normalize_event(evt: Dict) -> str:
    """Return a simple normalized message: lowercase, collapse spaces, strip punctuation where noisy."""
    msg_parts = []
    for k in ["message", "action", "status", "event_type"]:
        if k in evt and evt[k]:
            msg_parts.append(str(evt[k]))
    msg = " ".join(msg_parts) if msg_parts else str(evt)
    msg = msg.lower()
    msg = re.sub(r"\s+", " ", msg).strip()
    return msg
