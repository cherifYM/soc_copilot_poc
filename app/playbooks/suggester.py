
from typing import List
PLAYBOOKS = {
    "auth_failure": [
        "Check recent password change for the user.",
        "Review MFA enrollment and recent device logins.",
        "Temporarily lock account after threshold breaches.",
    ],
    "port_scan": [
        "Block offending IP at edge firewall.",
        "Run quick vuln scan on targeted subnet.",
        "Open incident with NOC for monitoring.",
    ],
    "default": [
        "Review logs and validate if benign.",
        "Add to allowlist/blocklist as needed.",
        "Document in ticket and close or escalate.",
    ]
}
def suggest_actions(event_type: str) -> List[str]:
    et = (event_type or "").lower()
    if "auth" in et or "login" in et: return PLAYBOOKS["auth_failure"]
    if "scan" in et or "nmap" in et: return PLAYBOOKS["port_scan"]
    return PLAYBOOKS["default"]
