"""Event records — full incident lifecycle with digital signature (FR-4.4)."""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlmodel import JSON, Column, Field, SQLModel

from app.models.user import utcnow


class EventState(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    MITIGATED = "mitigated"
    CLOSED = "closed"


class EventRecord(SQLModel, table=True):
    __tablename__ = "events"

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)
    tank_id: int | None = Field(default=None, foreign_key="tanks.id", index=True)
    alarm_id: int | None = Field(default=None, foreign_key="alarms.id")

    title: str = ""
    category: str = "safety"     # safety | leak | overfill | equipment | cyber
    severity: str = "medium"
    state: EventState = EventState.OPEN

    related_parameters: dict = Field(default_factory=dict, sa_column=Column(JSON))
    actions_taken: list = Field(default_factory=list, sa_column=Column(JSON))
    timeline: list = Field(default_factory=list, sa_column=Column(JSON))

    opened_by: str = ""
    closed_by: str | None = None
    closed_at: datetime | None = None
    digital_signature: str = ""
