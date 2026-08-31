"""Tanks, pipelines and configurable thresholds (FR-1.3, FR-1.5)."""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel

from app.models.user import utcnow


class TankStatus(str, Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"
    OFFLINE = "offline"


class Tank(SQLModel, table=True):
    __tablename__ = "tanks"

    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True)          # e.g. "TK-101"
    name: str = ""
    product: str = "crude"                              # stored product
    capacity_m3: float = 10000.0
    max_safe_level_pct: float = 90.0                    # API RP 2350 overfill protection
    critical_level_pct: float = 95.0
    diameter_m: float = 20.0

    # terminal map position (normalized 0..1) — UI-1
    map_x: float = 0.5
    map_y: float = 0.5
    zone: str = "A"

    status: TankStatus = TankStatus.GREEN
    digital_twin_enabled: bool = True
    created_at: datetime = Field(default_factory=utcnow)


class Pipeline(SQLModel, table=True):
    """Physical connection between tanks / manifolds — used by the GNN graph (FR-2.8)."""

    __tablename__ = "pipelines"

    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True)
    from_tank_id: int = Field(foreign_key="tanks.id", index=True)
    to_tank_id: int = Field(foreign_key="tanks.id", index=True)
    length_m: float = 100.0
    diameter_mm: float = 300.0
    max_flow_m3ph: float = 500.0


class Threshold(SQLModel, table=True):
    """Per-tank per-parameter alarm limits (FR-1.5)."""

    __tablename__ = "thresholds"

    id: int | None = Field(default=None, primary_key=True)
    tank_id: int = Field(foreign_key="tanks.id", index=True)
    parameter: str = Field(index=True)   # level | temperature | pressure | flammable_gas_ppm | h2s_ppm | ...
    lo_warn: float | None = None
    lo_critical: float | None = None
    hi_warn: float | None = None
    hi_critical: float | None = None
    unit: str = ""
    updated_by: str = "system"
    updated_at: datetime = Field(default_factory=utcnow)
