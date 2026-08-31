"""Time-series sensor readings (FR-1.1, FR-1.2).

On SQLite this is a plain table with a (tank_id, ts) index. On TimescaleDB the
deployment converts it to a hypertable (see backend/migrations/timescale.sql).
"""
from __future__ import annotations

from datetime import datetime

from sqlmodel import Field, SQLModel


class Reading(SQLModel, table=True):
    __tablename__ = "readings"

    id: int | None = Field(default=None, primary_key=True)
    tank_id: int = Field(foreign_key="tanks.id", index=True)
    ts: datetime = Field(index=True)

    # physical / chemical parameters (SRS 2.2, FR-1.1)
    level: float = 0.0                     # %
    temperature: float = 0.0              # °C
    pressure: float = 0.0                 # bar
    density: float = 0.0                  # kg/L
    flammable_gas_ppm: float = 0.0
    h2s_ppm: float = 0.0
    vibration_mm_s: float = 0.0
    corrosion_rate_mm_year: float = 0.0

    # patentable multimodal input (FR-1.7) — acoustic leak signature energy
    acoustic_db: float = 0.0
    acoustic_leak_band_ratio: float = 0.0  # energy ratio in the 20–60 kHz leak band

    # ground-truth label (only populated by the simulator / digital twin)
    leak_event: int = 0

    source: str = "sensor"                # sensor | twin | manual
