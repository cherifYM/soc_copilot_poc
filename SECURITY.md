<<<<<<< HEAD

### 4) `SECURITY.md`
```markdown
# Security Policy

## Supported versions
This is a PoC; security issues are fixed on `main`.

## Reporting a vulnerability
- Email: cherifymm@gmail.com
- Include: steps to reproduce, affected commit/branch, impact, logs if safe.
- We aim to respond within 72 hours.

## Data handling
- PII is **redacted on ingest**. Residency tag (**SA/AE**) is attached per event.
- Optional LLM summaries (v0.2.0) see **only redacted text**.
- Actions are **human approved**; approvals are **audited**.
=======
# Security Policy

## Supported versions
This is a PoC; we fix security issues on `main`.

## Reporting a vulnerability
- Email: security@yourdomain.tld
- Include: steps to reproduce, affected versions/commit, impact
- We aim to respond within 72 hours.

## Data handling
- PII is redacted on ingest; LLMs (when enabled) only see redacted text.
- Residency tags (SA/AE) are attached at ingest and preserved end-to-end.
>>>>>>> 01defdf (Initial code import (local state))
