# streamlit/app.py
import os
from typing import List

import requests
import streamlit as st

# Avoid requiring .streamlit/secrets.toml; use env var or default
API_BASE = os.getenv("API_BASE", "http://localhost:8000")

st.set_page_config(page_title="SOC Copilot PoC", layout="wide")
st.title("SOC Copilot — PoC")


def section_metrics():
    st.subheader("Metrics")
    try:
        r = requests.get(f"{API_BASE}/metrics", timeout=5)
        r.raise_for_status()
        data = r.json()
        c1, c2, c3 = st.columns(3)
        c1.metric("Events", data.get("events", 0))
        c2.metric("Incidents", data.get("incidents", 0))
        c3.metric("Suppression", f"{int(100*data.get('suppression_rate',0))}%")
    except Exception as e:
        st.warning(f"API not reachable at {API_BASE}: {e}")


def section_ingest():
    st.subheader("Ingest sample log")
    sample = {
        "source": "auth_service",
        "event_type": "auth_failure",
        "message": "Failed login for user john@example.com from 192.168.1.22",
        "region": "sa",
    }
    payload = {"events": [sample]}
    if st.button("Ingest sample event"):
        try:
            r = requests.post(f"{API_BASE}/ingest/logs", json=payload, timeout=5)
            r.raise_for_status()
            st.json(r.json())
        except Exception as e:
            st.error(f"Failed to ingest sample event: {e}")


def section_incidents():
    st.subheader("Incidents")
    try:
        r = requests.get(f"{API_BASE}/incidents", timeout=5)
        r.raise_for_status()
        rows: List[dict] = r.json()
    except Exception as e:
        st.error(f"Failed to load incidents: {e}")
        return

    for inc in rows:
        with st.expander(f"#{inc['id']} — {inc['title']} ({inc['count']})"):
            st.write(inc.get("summary", ""))
            c1, c2 = st.columns(2)
            if c1.button("Suggest actions", key=f"sugg_{inc['id']}"):
                try:
                    s = requests.post(f"{API_BASE}/incidents/{inc['id']}/suggest_actions", timeout=5)
                    s.raise_for_status()
                    st.json(s.json())
                except Exception as e:
                    st.error(f"Failed to suggest actions: {e}")
            with c2.form(key=f"approve_{inc['id']}"):
                action_name = st.text_input("Action name", value="Block IP at edge")
                notes = st.text_input("Notes", value="Approved in PoC UI")
                submit = st.form_submit_button("Approve action")
                if submit:
                    try:
                        res = requests.post(
                            f"{API_BASE}/incidents/{inc['id']}/approve_action",
                            json={"action_name": action_name, "notes": notes},
                            timeout=5,
                        )
                        res.raise_for_status()
                        st.json(res.json())
                    except Exception as e:
                        st.error(f"Failed to approve action: {e}")


section_metrics()
st.divider()
section_ingest()
st.divider()
section_incidents()
