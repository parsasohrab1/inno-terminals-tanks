"""Persisted leak predictions with explainability (FR-2.3, FR-2.4)."""
from __future__ import annotations

from datetime import datetime

from sqlmodel import JSON, Column, Field, SQLModel

from app.models.user import utcnow


class LeakPrediction(SQLModel, table=True):
    __tablename__ = "leak_predictions"

    id: int | None = Field(default=None, primary_key=True)
    tank_id: int = Field(foreign_key="tanks.id", index=True)
    ts: datetime = Field(default_factory=utcnow, index=True)

    probability: float = 0.0            # P(leak within horizon)
    horizon_minutes: int = 30
    confidence_low: float = 0.0
    confidence_high: float = 0.0
    will_leak: bool = False

    model_name: str = "baseline"       # baseline | gnn (proprietary)
    anomaly_score: float = 0.0

    # explainability — top contributing features (SHAP-lite / permutation)
    contributions: dict = Field(default_factory=dict, sa_column=Column(JSON))
    # GNN only: predicted propagation to neighbouring tanks
    propagation: dict = Field(default_factory=dict, sa_column=Column(JSON))
