"""Digital twin API (SRS 5.2, FR-2.7, FR-2.9)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.api.deps import get_current_user, require_roles
from app.database import get_session
from app.models.tank import Tank
from app.models.user import Role, User
from app.services import digital_twin

router = APIRouter()


@router.get("/state")
def all_twin_states(session: Session = Depends(get_session), _: User = Depends(get_current_user)):
    return [digital_twin.twin_state(session, t) for t in session.exec(select(Tank)).all()]


@router.get("/{tank_id}/state")
def twin_state(tank_id: int, session: Session = Depends(get_session),
               _: User = Depends(get_current_user)):
    t = session.get(Tank, tank_id)
    if not t:
        raise HTTPException(404, "tank not found")
    return digital_twin.twin_state(session, t)


class SimBody(BaseModel):
    minutes: int = 120
    leak: bool = True
    seed: int | None = None


@router.post("/{tank_id}/simulate")
def simulate(tank_id: int, body: SimBody, session: Session = Depends(get_session),
             _: User = Depends(require_roles(Role.SAFETY_ENGINEER, Role.OPS_MANAGER))):
    """FR-2.9 — run a labelled leak scenario for training / drills."""
    t = session.get(Tank, tank_id)
    if not t:
        raise HTTPException(404, "tank not found")
    return digital_twin.simulate(session, t, minutes=body.minutes, leak=body.leak, seed=body.seed)
