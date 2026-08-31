"""Immutable audit log (NFR-3.4) — every privileged action + config change."""
from __future__ import annotations

from datetime import datetime

from sqlmodel import JSON, Column, Field, SQLModel

from app.models.user import utcnow


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_log"

    id: int | None = Field(default=None, primary_key=True)
    ts: datetime = Field(default_factory=utcnow, index=True)
    username: str = Field(default="anonymous", index=True)
    role: str = ""
    action: str = Field(index=True)          # login | threshold.update | alarm.ack | operation.override | ...
    target: str = ""
    ip: str = ""
    detail: dict = Field(default_factory=dict, sa_column=Column(JSON))
    prev_hash: str = ""
    entry_hash: str = ""                      # hash chain for tamper evidence
