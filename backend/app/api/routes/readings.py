"""Reading ingest + time-series query (FR-1.1, FR-1.2, FR-1.4)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlmodel import Session, select

from app.api.deps import get_current_user
from app.database import get_session
from app.models.reading import Reading
from app.models.user import User
from app.services import ingest
from app.services.reporting import parameter_trend

router = APIRouter()


class ReadingIn(BaseModel):
    tank_code: str | None = None
    tank_id: int | None = None
    ts: datetime | None = None
    level: float = 0.0
    temperature: float = 0.0
    pressure: float = 0.0
    density: float = 0.0
    flammable_gas_ppm: float = 0.0
    h2s_ppm: float = 0.0
    vibration_mm_s: float = 0.0
    corrosion_rate_mm_year: float = 0.0
    acoustic_db: float = 0.0
    acoustic_leak_band_ratio: float = 0.0
    leak_event: int = 0
    source: str = "sensor"


class IngestBody(BaseModel):
    readings: list[ReadingIn]
    score: bool = True


@router.post("/ingest")
def ingest_readings(body: IngestBody, session: Session = Depends(get_session)):
    """Gateway ingest endpoint. In production this sits behind mutual-TLS on the
    industrial VLAN (COM-3); the simulator posts here directly."""
    return ingest.ingest_batch(
        session, [r.model_dump() for r in body.readings], score=body.score
    )


@router.get("/{tank_id}")
def query_readings(
    tank_id: int,
    hours: int = Query(1, ge=1, le=24 * 365),
    limit: int = Query(2000, le=20000),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    rows = session.exec(
        select(Reading).where(Reading.tank_id == tank_id, Reading.ts >= since)
        .order_by(Reading.ts.desc()).limit(limit)
    ).all()
    rows.reverse()
    return [r.model_dump() for r in rows]


@router.get("/{tank_id}/trend/{parameter}")
def trend(tank_id: int, parameter: str, hours: int = Query(24, ge=1, le=8760),
          session: Session = Depends(get_session), _: User = Depends(get_current_user)):
    return parameter_trend(session, tank_id, parameter, hours=hours)
