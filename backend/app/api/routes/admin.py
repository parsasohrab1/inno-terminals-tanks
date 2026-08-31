"""Admin: audit log, IP-vault status, model retraining, health (NFR-3.4, NFR-4.2)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app import secure
from app.api.deps import get_current_user, require_roles
from app.core.audit import verify_chain
from app.database import get_session
from app.models.audit import AuditLog
from app.models.user import Role, User

router = APIRouter()


@router.get("/audit")
def audit_log(limit: int = 200, session: Session = Depends(get_session),
              _: User = Depends(require_roles(Role.SAFETY_ENGINEER, Role.EXECUTIVE))):
    rows = session.exec(select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)).all()
    return {
        "chain_intact": verify_chain(session),
        "entries": [
            {"id": r.id, "ts": r.ts.isoformat(), "user": r.username, "role": r.role,
             "action": r.action, "target": r.target, "ip": r.ip, "detail": r.detail}
            for r in rows
        ],
    }


@router.get("/ip-vault")
def ip_vault_status(_: User = Depends(require_roles(Role.EXECUTIVE))):
    """Whether the proprietary/patentable modules are active in this deployment.

    The module *contents* are never exposed — only presence + unlock state.
    """
    st = secure.status()
    return {
        "vault_unlocked": st["vault_unlocked"],
        "encrypted_modules": st["encrypted_modules"],
        "active_features": {
            "gnn_multi_stage_leak_prediction": "gnn_leak.py.enc" in st["encrypted_modules"]
                                               and st["vault_unlocked"],
            "risk_aware_optimization": "risk_aware_optimizer.py.enc" in st["encrypted_modules"]
                                       and st["vault_unlocked"],
            "digital_twin_leak_simulation": "twin_leak_sim.py.enc" in st["encrypted_modules"]
                                            and st["vault_unlocked"],
            "multimodal_acoustic_detection": "multimodal_acoustic.py.enc" in st["encrypted_modules"]
                                             and st["vault_unlocked"],
        },
        "note": "Locked deployments run open baseline algorithms with full availability.",
    }


@router.post("/retrain")
def retrain(_: User = Depends(require_roles(Role.SAFETY_ENGINEER))):
    """FR-2.2 — trigger baseline model retraining."""
    from app.ml.train import load_corpus, _windows_from_frame
    from app.ml.model import LeakBaselineModel, reload_model

    df = load_corpus(None)
    X, y = _windows_from_frame(df)
    if len(X) == 0 or y.sum() == 0:
        return {"ok": False, "reason": "no usable training windows"}
    model = LeakBaselineModel()
    metrics = model.fit(X, y)
    model.save()
    reload_model()
    return {"ok": True, "metrics": metrics}


@router.get("/health")
def health(session: Session = Depends(get_session)):
    from app.services.realtime import hub

    return {
        "status": "ok",
        "db": "ok" if session.exec(select(User).limit(1)) is not None else "error",
        "ws_clients": hub.client_count,
        "ip_vault_unlocked": secure.available(),
    }
