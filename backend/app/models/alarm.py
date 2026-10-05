"""Alarm & event management (FR-4, ISA-18.2 alarm rationalization)."""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel

from app.models.user import utcnow


class AlarmSeverity(str, Enum):
    CRITICAL = "critical"   # critical
    HIGH = "high"           # high
    MEDIUM = "medium"       # medium
    LOW = "low"             # low

    @property
    def rank(self) -> int:
        return {"critical": 0, "high": 1, "medium": 2, "low": 3}[self.value]


class AlarmState(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    SUPPRESSED = "suppressed"      # FR-4.5 intelligent suppression
    SHELVED = "shelved"
    CLEARED = "cleared"


class Alarm(SQLModel, table=True):
    __tablename__ = "alarms"

    id: int | None = Field(default=None, primary_key=True)
    tank_id: int | None = Field(default=None, foreign_key="tanks.id", index=True)
    ts: datetime = Field(default_factory=utcnow, index=True)

    parameter: str = ""
    value: float | None = None
    limit: float | None = None
    severity: AlarmSeverity = AlarmSeverity.MEDIUM
    state: AlarmState = AlarmState.ACTIVE

    title: str = ""
    message: str = ""
    kind: str = "threshold"        # threshold | leak_prediction | leak_confirmed | deviation | system

    # de-duplication / suppression (FR-4.5)
    dedup_key: str = Field(default="", index=True)
    root_cause_id: int | None = Field(default=None, foreign_key="alarms.id")
    suppressed_reason: str | None = None

    # two-person rule for CRITICAL (FR-4.3)
    requires_two_person: bool = False
    cleared_at: datetime | None = None


class AlarmAck(SQLModel, table=True):
    __tablename__ = "alarm_acks"

    id: int | None = Field(default=None, primary_key=True)
    alarm_id: int = Field(foreign_key="alarms.id", index=True)
    user_id: int = Field(foreign_key="users.id")
    username: str = ""
    ts: datetime = Field(default_factory=utcnow)
    note: str = ""
    digital_signature: str = ""    # FR-4.4 — HMAC over (alarm_id,user,ts)
