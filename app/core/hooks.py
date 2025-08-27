# app/core/hooks.py
"""
SQLAlchemy hooks to enforce data invariants at the ORM layer.

Ensures every Event row gets attached to an Incident based on its cluster_key
before insert, preventing NULL incident_id errors.
"""
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.core.models import Event, Incident

print("[hooks] registering SQLAlchemy listeners")

@event.listens_for(Event, "before_insert")
def _attach_incident_before_insert(mapper, connection, target: Event):
    """Ensure target.incident_id is set using target.cluster_key."""
    if getattr(target, "incident_id", None) is not None:
        return

    cluster_key = getattr(target, "cluster_key", None)
    if not cluster_key:
        # Can't map to an incident without cluster_key; upstream should ensure it exists.
        return

    # Use a short-lived Session bound to the same connection performing the INSERT.
    db = Session(bind=connection)
    try:
        incident = db.query(Incident).filter_by(cluster_key=cluster_key).one_or_none()
        if incident is None:
            incident = Incident(cluster_key=cluster_key, status="open")
            db.add(incident)
            db.flush()  # ensure incident.id
        target.incident_id = incident.id
    finally:
        db.close()
