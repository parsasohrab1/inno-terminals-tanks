"""Append-only audit trail helper with a tamper-evident hash chain (NFR-3.4)."""
from __future__ import annotations

import json

from sqlmodel import Session, select

from app.core.security import chain_hash
from app.models.audit import AuditLog


def record(
    session: Session,
    *,
    username: str,
    role: str = "",
    action: str,
    target: str = "",
    ip: str = "",
    detail: dict | None = None,
) -> AuditLog:
    prev = session.exec(select(AuditLog).order_by(AuditLog.id.desc())).first()
    prev_hash = prev.entry_hash if prev else "genesis"
    detail = detail or {}
    payload = json.dumps(
        {"u": username, "a": action, "t": target, "d": detail}, sort_keys=True, default=str
    )
    entry = AuditLog(
        username=username,
        role=role,
        action=action,
        target=target,
        ip=ip,
        detail=detail,
        prev_hash=prev_hash,
        entry_hash=chain_hash(prev_hash, payload),
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


def verify_chain(session: Session) -> bool:
    prev_hash = "genesis"
    for entry in session.exec(select(AuditLog).order_by(AuditLog.id)):
        payload = json.dumps(
            {"u": entry.username, "a": entry.action, "t": entry.target, "d": entry.detail},
            sort_keys=True,
            default=str,
        )
        if chain_hash(prev_hash, payload) != entry.entry_hash:
            return False
        prev_hash = entry.entry_hash
    return True
