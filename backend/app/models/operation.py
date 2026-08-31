"""Loading / unloading operations & optimized schedule (FR-3)."""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlmodel import JSON, Column, Field, SQLModel

from app.models.user import utcnow


class OperationKind(str, Enum):
    LOADING = "loading"      # into tank
    UNLOADING = "unloading"  # out of tank


class OperationState(str, Enum):
    REQUESTED = "requested"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    ABORTED = "aborted"


class Operation(SQLModel, table=True):
    __tablename__ = "operations"

    id: int | None = Field(default=None, primary_key=True)
    ref: str = Field(index=True, default="")        # ERP/MES order reference (FR-3.4)
    tank_id: int = Field(foreign_key="tanks.id", index=True)
    kind: OperationKind = OperationKind.LOADING
    state: OperationState = OperationState.REQUESTED

    volume_m3: float = 1000.0
    flow_rate_m3ph: float = 300.0
    priority: int = 3                               # 1 (highest) .. 5
    pump_id: str = "P-1"

    earliest_start: datetime | None = None
    due_by: datetime | None = None

    # optimizer output
    planned_start: datetime | None = None
    planned_end: datetime | None = None
    predicted_leak_risk: float = 0.0               # FR-3.7 risk-aware objective input
    energy_kwh: float = 0.0                        # FR-3.6 energy term
    optimizer_run_id: str | None = Field(default=None, index=True)

    created_at: datetime = Field(default_factory=utcnow)
    meta: dict = Field(default_factory=dict, sa_column=Column(JSON))
