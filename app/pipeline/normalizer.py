
import re
from typing import Dict
def normalize_event(evt: Dict) -> str:
    parts = []
    for k in ["message", "action", "status", "event_type"]:
        v = evt.get(k)
        if v:
            parts.append(str(v))
    msg = " ".join(parts) if parts else str(evt)
    msg = msg.lower()
    msg = re.sub(r"\s+", " ", msg).strip()
    return msg
