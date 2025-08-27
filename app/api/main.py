# app/api/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from dotenv import load_dotenv
import os
import re

from app.core.db import Base, engine, get_db
from app.core import models
from app.pipeline.normalizer import normalize_event
from app.pipeline.pii_redactor import redact_pii, residency_tag, REDACTION_PATTERNS
from app.pipeline.clustering import cluster_key, incident_title, explain_cluster
from app.pipeline.summarizer import summarize_incident
from app.playbooks.suggester import suggest_actions
import app.core.hooks  # noqa: F401  # registers SQLAlchemy listeners on import

# ----- Setup -----
load_dotenv()
Base.metadata.create_all(bind=engine)

app = FastAPI(title="SOC Copilot PoC", version="0.1.0")

# CORS: allow list from env (fallback "*")
origins = [o for o in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",") if o]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_TAG = os.getenv("DEFAULT_RESIDENCY_TAG", "SA")
STORE_RAW = os.getenv("STORE_RAW", "false").lower() == "true"
BENIGN_TYPES = {
    t.strip().lower()
    for t in os.getenv("BENIGN_TYPES", "auth_success").split(",")
    if t.strip()
}
CRITICAL_TYPES = {
    t.strip().lower()
    for t in os.getenv(
        "CRITICAL_TYPES",
        "auth_failure,mfa_bypass,api_key_use,privilege_escalation",
    ).split(",")
    if t.strip()
}

# ----- Schemas -----
class LogEvent(BaseModel):
    source: str = Field("app", description="Emitter/source")
    event_type: str = Field("auth_failure", description="Type of event")
    message: str = Field(..., description="Message payload")
    user: Optional[str] = None
    ip: Optional[str] = None
    email: Optional[str] = None
    region: Optional[str] = None
    action: Optional[str] = None
    status: Optional[str] = None
    ts: Optional[str] = Field(
        None,
        description="Optional ISO 8601 timestamp for clustering; falls back to ingest time",
    )

class IngestRequest(BaseModel):
    events: List[LogEvent]

class ApproveRequest(BaseModel):
    action_name: str
    notes: Optional[str] = ""

# ----- Endpoints -----
@app.post("/ingest/logs")
def ingest_logs(payload: IngestRequest, db: Session = Depends(get_db)):
    created = 0
    for e in payload.events:
        evt = e.dict()

        # Redact before clustering/summarizing
        red, _ = redact_pii(evt.get("message", ""))
        tag = residency_tag(evt, DEFAULT_TAG)
        norm_cluster = normalize_event({**evt, "message": red})
        ck = cluster_key(evt, norm_cluster)
        et_lower = (e.event_type or "").lower()

        # Benign → attach to incident; if new, create as status="noise"
        if et_lower in BENIGN_TYPES and et_lower not in CRITICAL_TYPES:
            incident = (
                db.query(models.Incident)
                .filter(models.Incident.cluster_key == ck)
                .first()
            )
            if not incident:
                incident = models.Incident(
                    title=incident_title(evt),
                    cluster_key=ck,
                    summary="",
                    count=0,
                    status="noise",  # noise incidents excluded from "active" metrics
                )
                db.add(incident)
                db.flush()

            ev = models.Event(
                source=e.source,
                event_type=e.event_type,
                raw=e.message if STORE_RAW else "",
                normalized=norm_cluster,
                redacted=red,
                residency_tag=tag,
                cluster_key=ck,
                incident_id=incident.id,
            )
            db.add(ev)
            incident.count += 1
            incident.summary = summarize_incident(red, incident.count)

            # --- Promotion safety net: fail→success burst detection ---
            try:
                if incident.status == "noise":
                    recent = (
                        db.query(models.Event)
                        .filter(models.Event.cluster_key == ck)
                        .order_by(models.Event.id.desc())
                        .limit(8)
                        .all()
                    )
                    failures = sum(
                        1 for r in recent if (r.event_type or "").lower() == "auth_failure"
                    )
                    has_recent_success = any(
                        (r.event_type or "").lower() == "auth_success" for r in recent[:2]
                    )
                    if failures >= 5 and has_recent_success:
                        incident.status = "open"
                        incident.summary = (
                            f"Promotion: {failures} failures then success "
                            f"(possible credential stuffing → takeover)"
                        )
            except Exception:
                # never break ingest on heuristic issues
                pass

            created += 1
            continue

        # Non-benign (or critical) → normal open incident (get-or-create)
        incident = (
            db.query(models.Incident)
            .filter(models.Incident.cluster_key == ck)
            .first()
        )
        if not incident:
            incident = models.Incident(
                title=incident_title(evt),
                cluster_key=ck,
                summary="",
                count=0,
                status="open",
            )
            db.add(incident)
            db.flush()

        ev = models.Event(
            source=e.source,
            event_type=e.event_type,
            raw=e.message if STORE_RAW else "",
            normalized=norm_cluster,
            redacted=red,
            residency_tag=tag,
            cluster_key=ck,
            incident_id=incident.id,
        )
        db.add(ev)
        incident.count += 1
        incident.summary = summarize_incident(red, incident.count)
        created += 1

    db.commit()

    # Quick summary in response
    total_events = db.query(models.Event).count()
    total_incidents = db.query(models.Incident).count()
    suppression_rate = 1.0 - (total_incidents / total_events) if total_events else 0.0
    return {
        "ingested": created,
        "events": total_events,
        "incidents": total_incidents,
        "suppression_rate": round(suppression_rate, 3),
    }

@app.get("/incidents")
def list_incidents(db: Session = Depends(get_db)):
    rows = db.query(models.Incident).order_by(models.Incident.last_seen.desc()).all()
    return [
        {
            "id": r.id,
            "title": r.title,
            "summary": r.summary,
            "count": r.count,
            "status": r.status,
        }
        for r in rows
    ]

@app.get("/incidents/{incident_id}")
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    inc = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(404, "Incident not found")
    sample = (
        db.query(models.Event)
        .filter(models.Event.incident_id == incident_id)
        .order_by(models.Event.id.desc())
        .first()
    )
    return {
        "id": inc.id,
        "title": inc.title,
        "summary": inc.summary,
        "count": inc.count,
        "status": inc.status,
        "sample_redacted": sample.redacted if sample else "",
    }

@app.get("/evidence/incident/{incident_id}")
def incident_evidence(incident_id: int, db: Session = Depends(get_db)):
    """Return incident evidence, redaction stats, approvals and why it clustered."""
    inc = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(404, "incident not found")

    events = (
        db.query(models.Event)
        .filter(models.Event.incident_id == incident_id)
        .order_by(models.Event.id.desc())
        .limit(50)
        .all()
    )

    # why-clustered (uses normalized text from latest event)
    why = {}
    if events:
        latest = events[0]
        why = explain_cluster(
            {"event_type": latest.event_type, "user": None, "ip": None, "ts": None},
            latest.normalized,
        )

    # Aggregate redaction counts using shared patterns
    redaction_aggregate = {}
    for ev in events:
        s = ev.redacted or ""
        for k, pat in REDACTION_PATTERNS.items():
            c = len(pat.findall(s))
            if c:
                redaction_aggregate[k] = redaction_aggregate.get(k, 0) + c

    approvals = (
        db.query(models.Approval)
        .filter(models.Approval.incident_id == incident_id)
        .order_by(models.Approval.id.asc())
        .all()
    )

    return {
        "incident_id": inc.id,
        "cluster_key": inc.cluster_key,
        "status": inc.status,
        "count": inc.count,
        "why_clustered": why,
        "event_sample": [e.redacted for e in events[:3]],
        "redaction_aggregate": redaction_aggregate,
        "approvals": [
            {"id": a.id, "action_name": a.action_name, "notes": a.notes}
            for a in approvals
        ],
    }

@app.get("/incidents/by-event/{event_id}")
def incident_by_event(event_id: int, db: Session = Depends(get_db)):
    ev = db.get(models.Event, event_id)
    if not ev:
        raise HTTPException(404, "event not found")
    inc = db.get(models.Incident, ev.incident_id) if ev.incident_id else None
    if not inc:
        raise HTTPException(404, "incident not found")
    return {"incident_id": inc.id, "cluster_key": inc.cluster_key, "status": inc.status}

@app.get("/incidents/by-cluster/{ck}")
def incident_by_cluster(ck: str, db: Session = Depends(get_db)):
    inc = db.query(models.Incident).filter(models.Incident.cluster_key == ck).first()
    if not inc:
        raise HTTPException(404, "incident not found")
    return {
        "incident_id": inc.id,
        "cluster_key": inc.cluster_key,
        "status": inc.status,
        "count": inc.count,
    }

@app.post("/incidents/{incident_id}/suggest_actions")
def suggest_incident_actions(incident_id: int, db: Session = Depends(get_db)):
    inc = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(404, "Incident not found")
    ev = (
        db.query(models.Event)
        .filter(models.Event.incident_id == incident_id)
        .order_by(models.Event.id.desc())
        .first()
    )
    actions = suggest_actions(ev.event_type if ev else "")
    return {"incident_id": incident_id, "actions": actions}

@app.post("/incidents/{incident_id}/approve_action")
def approve_action(incident_id: int, req: ApproveRequest, db: Session = Depends(get_db)):
    inc = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(404, "Incident not found")
    rec = models.Approval(
        incident_id=incident_id,
        action_name=req.action_name,
        notes=req.notes or "",
    )
    db.add(rec)
    db.commit()
    return {"ok": True, "approval_id": rec.id}

@app.get("/events/recent")
def events_recent(limit: int = 50, db: Session = Depends(get_db)):
    rows = (
        db.query(models.Event)
        .options(joinedload(models.Event.incident))  # prefetch incidents to avoid N+1
        .order_by(models.Event.id.desc())
        .limit(max(1, min(limit, 500)))
        .all()
    )
    return [
        {
            "id": r.id,
            "incident_id": r.incident_id,
            "event_type": r.event_type,
            "incident_status": r.incident.status if r.incident else None,
            "redacted": r.redacted,
        }
        for r in rows
    ]

@app.get("/metrics")
def metrics(db: Session = Depends(get_db)):
    total_events = db.query(models.Event).count()
    total_incidents = db.query(models.Incident).count()

    # Duplicate count by cluster
    rows = (
        db.query(models.Event.cluster_key, func.count(models.Event.id))
        .group_by(models.Event.cluster_key)
        .all()
    )
    suppressed_events = sum(max(0, cnt - 1) for _, cnt in rows)

    # Active incidents = exclude 'noise'
    incidents_active = (
        db.query(models.Incident)
        .filter(models.Incident.status != "noise")
        .count()
    )

    suppression_rate = 1.0 - (total_incidents / total_events) if total_events else 0.0
    suppression_rate_active = (
        1.0 - (incidents_active / total_events) if total_events else 0.0
    )
    dup_rate = (suppressed_events / total_events) if total_events else 0.0

    return {
        "events": total_events,
        "incidents": total_incidents,
        "incidents_active": incidents_active,
        "suppressed_events": suppressed_events,
        "suppression_rate": round(suppression_rate, 3),
        "suppression_rate_active": round(suppression_rate_active, 3),
        "dup_rate": round(dup_rate, 3),
    }

@app.get("/evidence/{event_id}")
def evidence(event_id: int, db: Session = Depends(get_db)):
    ev = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not ev:
        raise HTTPException(404, "Event not found")
    return {
        "event_id": ev.id,
        "residency_tag": ev.residency_tag,
        "redacted": ev.redacted,
        "incident_id": ev.incident_id,
        "cluster_key": ev.cluster_key,
    }

# Friendly aliases (no breaking change)
@app.get("/events/{event_id}/evidence")
def evidence_alias(event_id: int, db: Session = Depends(get_db)):
    return evidence(event_id, db)

@app.get("/incidents/{incident_id}/evidence")
def incident_evidence_alias(incident_id: int, db: Session = Depends(get_db)):
    return incident_evidence(incident_id, db)

@app.get("/health")
def health():
    return {"ok": True}
