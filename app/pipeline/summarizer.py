
def summarize_incident(sample_redacted: str, count: int) -> str:
    snippet = (sample_redacted[:120] + "…") if len(sample_redacted) > 120 else sample_redacted
    return f"Repeated event clustered ({count} hits). Example: {snippet}"
