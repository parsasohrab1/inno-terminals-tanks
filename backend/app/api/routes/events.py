"""Incident/event lifecycle with digital signature (FR-4.4)."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlmodel import Session, select

from app.api.deps import client_ip, get_current_user
from app.core import audit
from app.core.security import digital_signature
from app.database import get_session
from app.models.event import EventRecord, EventState
from app.models.user import User

router = APIRouter()


class EventCreate(BaseModel):
    title: str
    tank_id: int | None = None
    alarm_id: int | None = None
    category: str = "safety"
    severity: str = "medium"
    related_parameters: dict = {}


class ActionBody(BaseModel):
    action: str


@router.get("")
def list_events(state: EventState | None = None, session: Session = Depends(get_session),
                _: User = Depends(get_current_user)):
    q = select(EventRecord).order_by(EventRecord.created_at.desc())
    if state:
        q = q.where(EventRecord.state == state)
    return session.exec(q.limit(300)).all()


@router.post("")
def create_event(body: EventCreate, request: Request, session: Session = Depends(get_session),
                 user: User = Depends(get_current_user)):
    ev = EventRecord(
        title=body.title, tank_id=body.tank_id, alarm_id=body.alarm_id,
        category=body.category, severity=body.severity,
        related_parameters=body.related_parameters, opened_by=user.username,
        timeline=[{"ts": datetime.now(timezone.utc).isoformat(), "by": user.username,
                   "note": "event opened"}],
    )
    session.add(ev)
    session.commit()
    session.refresh(ev)
    audit.record(session, username=user.username, role=user.role.value,
                 action="event.create", target=f"event:{ev.id}", ip=client_ip(request))
    return ev


@router.post("/{event_id}/action")
def add_action(event_id: int, body: ActionBody, session: Session = Depends(get_session),
               user: User = Depends(get_current_user)):
    ev = session.get(EventRecord, event_id)
    if not ev:
        raise HTTPException(404, "event not found")
    ts = datetime.now(timezone.utc).isoformat()
    ev.actions_taken = [*ev.actions_taken, {"ts": ts, "by": user.username, "action": body.action}]
    ev.timeline = [*ev.timeline, {"ts": ts, "by": user.username, "note": body.action}]
    if ev.state == EventState.OPEN:
        ev.state = EventState.INVESTIGATING
    session.add(ev)
    session.commit()
    session.refresh(ev)
    return ev


@router.post("/{event_id}/close")
def close_event(event_id: int, request: Request, session: Session = Depends(get_session),
                user: User = Depends(get_current_user)):
    ev = session.get(EventRecord, event_id)
    if not ev:
        raise HTTPException(404, "event not found")
    ev.state = EventState.CLOSED
    ev.closed_by = user.username
    ev.closed_at = datetime.now(timezone.utc)
    ev.digital_signature = digital_signature(ev.id, user.username, ev.closed_at.isoformat())
    ev.timeline = [*ev.timeline, {"ts": ev.closed_at.isoformat(), "by": user.username,
                                  "note": "event closed + signed"}]
    session.add(ev)
    audit.record(session, username=user.username, role=user.role.value,
                 action="event.close", target=f"event:{event_id}", ip=client_ip(request))
    session.commit()
    session.refresh(ev)
    return ev
