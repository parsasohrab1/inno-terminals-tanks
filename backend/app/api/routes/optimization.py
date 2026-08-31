"""Loading/unloading optimization API (FR-3)."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlmodel import Session, select

from app.api.deps import client_ip, get_current_user, require_roles
from app.core import audit
from app.database import get_session
from app.models.operation import Operation, OperationKind, OperationState
from app.models.user import Role, User
from app.services import optimizer

router = APIRouter()


class OperationIn(BaseModel):
    ref: str = ""
    tank_id: int
    kind: OperationKind = OperationKind.LOADING
    volume_m3: float = 1000.0
    flow_rate_m3ph: float = 300.0
    priority: int = 3
    earliest_start: datetime | None = None
    due_by: datetime | None = None


@router.get("/operations")
def list_operations(session: Session = Depends(get_session), _: User = Depends(get_current_user)):
    return session.exec(select(Operation).order_by(Operation.created_at.desc())).all()


@router.post("/operations")
def create_operation(body: OperationIn, request: Request, session: Session = Depends(get_session),
                     user: User = Depends(require_roles(Role.OPS_MANAGER, Role.OPERATOR))):
    op = Operation(**body.model_dump())
    session.add(op)
    session.commit()
    session.refresh(op)
    audit.record(session, username=user.username, role=user.role.value,
                 action="operation.create", target=f"operation:{op.id}", ip=client_ip(request))
    return op


@router.post("/plan")
def build_plan(request: Request, pump_count: int = 3,
               session: Session = Depends(get_session),
               user: User = Depends(require_roles(Role.OPS_MANAGER))):
    plan = optimizer.build_plan(session, pump_count=pump_count)
    audit.record(session, username=user.username, role=user.role.value,
                 action="optimization.plan", target=f"run:{plan['run_id']}",
                 ip=client_ip(request), detail={"risk_aware": plan["risk_aware"],
                                                "makespan_min": plan["makespan_minutes"]})
    return plan


class WhatIfBody(BaseModel):
    disabled_pumps: list[str] = []
    extra_ops: list[dict] = []
    pump_count: int = 3


@router.post("/what-if")
def what_if(body: WhatIfBody, session: Session = Depends(get_session),
            _: User = Depends(get_current_user)):
    """FR-3.3 — scenario simulation (does not persist)."""
    return optimizer.what_if(
        session, disabled_pumps=body.disabled_pumps,
        extra_ops=body.extra_ops, pump_count=body.pump_count,
    )


@router.post("/operations/{op_id}/state")
def set_state(op_id: int, state: OperationState, session: Session = Depends(get_session),
              user: User = Depends(require_roles(Role.OPS_MANAGER, Role.OPERATOR))):
    op = session.get(Operation, op_id)
    if not op:
        raise HTTPException(404, "operation not found")
    op.state = state
    session.add(op)
    session.commit()
    session.refresh(op)
    return op
