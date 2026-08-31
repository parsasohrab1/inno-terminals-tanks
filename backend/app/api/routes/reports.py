"""Reporting & analytics API (FR-5)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.api.deps import get_current_user
from app.database import get_session
from app.models.user import User
from app.services import reporting

router = APIRouter()


@router.get("/kpi")
def kpi(days: int = Query(7, ge=1, le=90), session: Session = Depends(get_session),
        _: User = Depends(get_current_user)):
    return reporting.kpi_summary(session, days=days)


@router.get("/compliance")
def compliance(session: Session = Depends(get_session), _: User = Depends(get_current_user)):
    """FR-5.4 — API RP 2350 / IEC 61511 compliance evidence."""
    return reporting.compliance_report(session)
