"""Integration with existing systems — DCS/SCADA (OPC-UA), CMMS, ERP (FR-6).

These are working REST stubs modelling the ISA-95 exchange contract; a real
deployment binds them to an OPC-UA client and the site ERP/CMMS connectors.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, select

from app.api.deps import get_current_user, require_roles
from app.database import get_session
from app.models.operation import Operation, OperationKind, OperationState
from app.models.reading import Reading
from app.models.tank import Tank
from app.models.user import Role, User

router = APIRouter()


@router.get("/opcua/nodes")
def opcua_nodes(session: Session = Depends(get_session), _: User = Depends(get_current_user)):
    """OPC-UA address space projection (FR-6.1 / SW-2)."""
    nodes = []
    for t in session.exec(select(Tank)).all():
        r = session.exec(
            select(Reading).where(Reading.tank_id == t.id).order_by(Reading.ts.desc())
        ).first()
        for param in ("level", "temperature", "pressure", "flammable_gas_ppm"):
            nodes.append({
                "nodeId": f"ns=2;s=Terminal.{t.code}.{param}",
                "displayName": f"{t.code} {param}",
                "value": round(getattr(r, param), 3) if r else None,
                "dataType": "Double",
                "sourceTimestamp": r.ts.isoformat() if r else None,
            })
    return {"serverStatus": "running", "nodeCount": len(nodes), "nodes": nodes}


class ERPOrder(BaseModel):
    ref: str
    tank_code: str
    kind: OperationKind = OperationKind.LOADING
    volume_m3: float
    flow_rate_m3ph: float = 300.0
    priority: int = 3


@router.post("/erp/orders")
def erp_order(order: ERPOrder, session: Session = Depends(get_session),
              _: User = Depends(require_roles(Role.OPS_MANAGER))):
    """FR-3.4 / FR-6.3 — ERP pushes a loading order; we create an Operation."""
    tank = session.exec(select(Tank).where(Tank.code == order.tank_code)).first()
    if not tank:
        return {"accepted": False, "reason": "unknown tank"}
    op = Operation(
        ref=order.ref, tank_id=tank.id, kind=order.kind, volume_m3=order.volume_m3,
        flow_rate_m3ph=order.flow_rate_m3ph, priority=order.priority,
        state=OperationState.REQUESTED, meta={"origin": "ERP"},
    )
    session.add(op)
    session.commit()
    session.refresh(op)
    return {"accepted": True, "operation_id": op.id, "ref": op.ref}


@router.get("/cmms/work-orders")
def cmms_work_orders(session: Session = Depends(get_session), _: User = Depends(get_current_user)):
    """FR-6.2 — preventive work orders derived from equipment health (RCM / ISO 14224)."""
    orders = []
    for t in session.exec(select(Tank)).all():
        r = session.exec(
            select(Reading).where(Reading.tank_id == t.id).order_by(Reading.ts.desc())
        ).first()
        if not r:
            continue
        if r.vibration_mm_s > 5.0:
            orders.append({"tank": t.code, "type": "vibration-inspection",
                           "priority": "high", "reason": f"vibration {r.vibration_mm_s:.1f} mm/s"})
        if r.corrosion_rate_mm_year > 0.15:
            orders.append({"tank": t.code, "type": "wall-thickness-survey",
                           "priority": "medium",
                           "reason": f"corrosion {r.corrosion_rate_mm_year:.3f} mm/yr"})
    return {"generated_at": datetime.now(timezone.utc).isoformat(), "work_orders": orders}


@router.get("/isa95/equipment-hierarchy")
def isa95_hierarchy(session: Session = Depends(get_session), _: User = Depends(get_current_user)):
    """FR-6.4 — ISA-95 enterprise/site/area/work-unit model."""
    zones: dict[str, list] = {}
    for t in session.exec(select(Tank)).all():
        zones.setdefault(t.zone, []).append({"workUnit": t.code, "product": t.product})
    return {
        "enterprise": "INNO Petrochemical",
        "site": "Terminal-1",
        "areas": [{"area": f"Zone-{z}", "workUnits": u} for z, u in sorted(zones.items())],
    }
