import streamlit as st
import requests
import os
from typing import List

API_BASE = os.getenv("API_BASE", "http://localhost:8000")
import streamlit as st
import requests
import os
import os
from typing import List

# Avoid requiring .streamlit/secrets.toml; use env var or default
API_BASE = os.getenv("API_BASE", "http://localhost:8000")

st.set_page_config(page_title="SOC Copilot PoC", layout="wide")

st.title("SOC Copilot — PoC")


def section_metrics():
    st.subheader("Metrics")
    try:
        r = requests.get(f"{API_BASE}/metrics", timeout=5)
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
        r = requests.post(f"{API_BASE}/ingest/logs", json=payload)
        st.json(r.json())


def section_incidents():
    st.subheader("Incidents")
    r = requests.get(f"{API_BASE}/incidents")
    rows: List[dict] = r.json()
    for inc in rows:
        with st.expander(f"#{inc['id']} — {inc['title']} ({inc['count']})"):
            st.write(inc["summary"])            
            c1, c2 = st.columns(2)
            if c1.button("Suggest actions", key=f"sugg_{inc['id']}"):
                s = requests.post(f"{API_BASE}/incidents/{inc['id']}/suggest_actions")
                st.json(s.json())
            with c2.form(key=f"approve_{inc['id']}"):
                action_name = st.text_input("Action name", value="Block IP at edge")
                notes = st.text_input("Notes", value="Approved in PoC UI")
                submit = st.form_submit_button("Approve action")
                if submit:
                    res = requests.post(f"{API_BASE}/incidents/{inc['id']}/approve_action", json={"action_name": action_name, "notes": notes})
                    st.json(res.json())


section_metrics()
st.divider()
section_ingest()
st.divider()
section_incidents()
