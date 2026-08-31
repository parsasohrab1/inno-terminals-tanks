"""Leak prediction orchestration (FR-2).

Pipeline per tank:
  1. baseline model  (IsolationForest + GBDT + rules) — always available
  2. multimodal acoustic+vibration detector (proprietary #4) — if vault unlocked
  3. GNN spatial/propagation model (proprietary #1)          — if vault unlocked
  4. blend → persist LeakPrediction → raise alarm / ESD command as needed
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from app import secure
from app.config import settings
from app.ml.features import window_features
from app.ml.model import get_model
from app.models.alarm import AlarmSeverity, AlarmState
from app.models.prediction import LeakPrediction
from app.models.reading import Reading
from app.models.tank import Pipeline, Tank
from app.services import alarm_engine

WINDOW = 60


def _recent_window(session: Session, tank_id: int, n: int = WINDOW) -> list[dict]:
    rows = session.exec(
        select(Reading).where(Reading.tank_id == tank_id).order_by(Reading.ts.desc()).limit(n)
    ).all()
    rows.reverse()
    return [r.model_dump() for r in rows]


def _confirmed_leak(window: list[dict]) -> bool:
    """FR-2.5 — real leak from gas sensors / pressure drop."""
    if len(window) < 5:
        return False
    last = window[-1]
    first = window[max(0, len(window) - 10)]
    gas_spike = last["flammable_gas_ppm"] >= 80 or last["h2s_ppm"] >= 10
    pressure_drop = (first["pressure"] - last["pressure"]) >= 0.25
    return gas_spike and pressure_drop


def predict_tank(session: Session, tank: Tank, *, persist: bool = True) -> LeakPrediction:
    window = _recent_window(session, tank.id)
    feats = window_features(window)

    base = get_model().predict_one(feats)
    prob = base["probability"]
    anomaly = base["anomaly_score"]
    contributions = dict(base["contributions"])
    model_name = base["model_name"]
    propagation: dict = {}

    # --- proprietary #4: multimodal acoustic+vibration ---
    mm = secure.load("multimodal_acoustic")
    if mm is not None and window:
        det = mm.build().score(window)
        prob = max(prob, 0.5 * prob + 0.5 * det["score"])
        contributions["acoustic_fusion"] = round(det["acoustic_contribution"], 3)
        contributions["vibration_fusion"] = round(det["vibration_contribution"], 3)
        model_name = "baseline+multimodal"

    # --- proprietary #1: GNN spatial + propagation ---
    gnn = secure.load("gnn_leak")
    if gnn is not None:
        nodes = {tank.id: window}
        edges = []
        pipes = session.exec(
            select(Pipeline).where(
                (Pipeline.from_tank_id == tank.id) | (Pipeline.to_tank_id == tank.id)
            )
        ).all()
        for p in pipes:
            other = p.to_tank_id if p.from_tank_id == tank.id else p.from_tank_id
            nodes.setdefault(other, _recent_window(session, other))
            edges.append(p.model_dump())
        result = gnn.build().predict(nodes, edges, settings.leak_horizon_minutes)
        g = result.get(tank.id, {})
        if g:
            prob = float(max(prob, 0.4 * prob + 0.6 * g["probability"]))
            anomaly = max(anomaly, abs(g.get("anomaly_score", 0.0)) / 5.0)
            propagation = g.get("propagation", {})
            for k, v in g.get("contributions", {}).items():
                contributions[f"gnn:{k}"] = round(float(v), 4)
            model_name = "gnn-ensemble"

    confirmed = _confirmed_leak(window)
    if confirmed:
        prob = max(prob, 0.97)

    horizon = settings.leak_horizon_minutes
    spread = 0.5 * (1 - prob) + 0.05
    pred = LeakPrediction(
        tank_id=tank.id,
        probability=round(prob, 4),
        horizon_minutes=horizon,
        confidence_low=round(max(0.0, prob - spread), 4),
        confidence_high=round(min(1.0, prob + spread), 4),
        will_leak=prob >= 0.85,
        model_name=model_name,
        anomaly_score=round(anomaly, 4),
        contributions=_topk(contributions),
        propagation={str(k): round(float(v), 3) for k, v in propagation.items()},
    )
    if persist:
        session.add(pred)
        session.commit()
        session.refresh(pred)

    _maybe_alarm(session, tank, pred, confirmed)
    return pred


def _topk(d: dict, k: int = 8) -> dict:
    return dict(sorted(d.items(), key=lambda kv: -abs(kv[1]))[:k])


def _maybe_alarm(session: Session, tank: Tank, pred: LeakPrediction, confirmed: bool) -> None:
    if confirmed:
        alarm_engine.raise_alarm(
            session,
            tank_id=tank.id,
            parameter="leak",
            value=pred.probability,
            severity=AlarmSeverity.CRITICAL,
            kind="leak_confirmed",
            title=f"{tank.code} — CONFIRMED LEAK",
            message="Gas spike + pressure drop detected. ESD valve isolation command issued (FR-2.5).",
            dedup_key=f"leak_confirmed:{tank.id}",
        )
        _issue_esd(session, tank)
        return

    if pred.probability >= 0.85:
        top = ", ".join(list(pred.contributions)[:3])
        alarm_engine.raise_alarm(
            session,
            tank_id=tank.id,
            parameter="leak",
            value=pred.probability,
            severity=AlarmSeverity.HIGH,
            kind="leak_prediction",
            title=f"{tank.code} — leak predicted ({pred.probability:.0%}) within {pred.horizon_minutes} min",
            message=f"Model {pred.model_name}. Top drivers: {top}.",
            dedup_key=f"leak_pred:{tank.id}",
        )


def _issue_esd(session: Session, tank: Tank) -> None:
    """FR-2.5 — emergency shutdown / valve isolation command stub (IEC 61511 SIS).

    A real deployment writes this to the Safety PLC over the SIS interface; here
    it is recorded as an event action and broadcast.
    """
    from app.models.event import EventRecord, EventState

    ev = EventRecord(
        tank_id=tank.id,
        title=f"ESD isolation — {tank.code}",
        category="leak",
        severity="critical",
        state=EventState.MITIGATED,
        actions_taken=[{"ts": datetime.now(timezone.utc).isoformat(),
                        "action": "ESD valve isolation command issued to Safety PLC",
                        "auto": True}],
        opened_by="leak-prediction-service",
    )
    session.add(ev)
    session.commit()


def sweep(session: Session) -> list[LeakPrediction]:
    """Score every tank — called by the scheduler and after ingest bursts."""
    preds = []
    for tank in session.exec(select(Tank)).all():
        preds.append(predict_tank(session, tank))
    return preds


def risk_at(session: Session, tank_id: int, at_time: datetime) -> float:
    """Risk estimate for the optimizer (FR-3.7). Uses the latest prediction and
    decays/keeps it over the requested horizon."""
    pred = session.exec(
        select(LeakPrediction)
        .where(LeakPrediction.tank_id == tank_id)
        .order_by(LeakPrediction.ts.desc())
    ).first()
    if not pred:
        return 0.0
    age_min = (at_time.replace(tzinfo=None) - pred.ts.replace(tzinfo=None)).total_seconds() / 60.0
    if age_min <= pred.horizon_minutes:
        return float(pred.probability)
    # beyond horizon: decay toward baseline
    decay = 0.5 ** ((age_min - pred.horizon_minutes) / 120.0)
    return float(pred.probability * decay)
