"""Reporting & analytics (FR-5) — KPIs, trends, compliance summaries."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, func, select

from app.models.alarm import Alarm, AlarmAck, AlarmState
from app.models.event import EventRecord
from app.models.operation import Operation, OperationState
from app.models.prediction import LeakPrediction
from app.models.reading import Reading
from app.models.tank import Tank
from app.services.alarm_engine import operator_alarm_rate


def kpi_summary(session: Session, *, days: int = 7) -> dict:
    since = datetime.now(timezone.utc) - timedelta(days=days)

    alarms = session.exec(select(Alarm).where(Alarm.ts >= since)).all()
    by_sev = Counter(a.severity.value for a in alarms)
    acks = session.exec(select(AlarmAck).where(AlarmAck.ts >= since)).all()

    # mean response time = ack.ts - alarm.ts
    alarm_ts = {a.id: a.ts for a in alarms}
    resp = [
        (ack.ts - alarm_ts[ack.alarm_id]).total_seconds()
        for ack in acks if ack.alarm_id in alarm_ts
    ]
    mean_resp = round(sum(resp) / len(resp), 1) if resp else None

    preds = session.exec(select(LeakPrediction).where(LeakPrediction.ts >= since)).all()
    fired = [p for p in preds if p.will_leak]
    # a prediction is "correct" if a confirmed-leak alarm exists for that tank within the horizon
    confirmed = session.exec(
        select(Alarm).where(Alarm.kind == "leak_confirmed", Alarm.ts >= since)
    ).all()
    confirmed_tanks = {a.tank_id for a in confirmed}
    true_pos = sum(1 for p in fired if p.tank_id in confirmed_tanks)

    ops = session.exec(select(Operation).where(Operation.created_at >= since)).all()
    completed = [o for o in ops if o.state == OperationState.COMPLETED]

    events = session.exec(select(EventRecord).where(EventRecord.created_at >= since)).all()

    return {
        "window_days": days,
        "safety": {
            "alarms_total": len(alarms),
            "alarms_by_severity": dict(by_sev),
            "alarms_suppressed": sum(1 for a in alarms if a.state == AlarmState.SUPPRESSED),
            "mean_response_seconds": mean_resp,
            "isa_18_2": operator_alarm_rate(session),
            "open_events": sum(1 for e in events if e.state.value != "closed"),
        },
        "leak_prediction": {
            "predictions": len(preds),
            "alerts_fired": len(fired),
            "confirmed_leaks": len(confirmed),
            "true_positives": true_pos,
            "false_positives": max(0, len(fired) - true_pos),
            "precision_est": round(true_pos / len(fired), 3) if fired else None,
        },
        "operations": {
            "requested": len(ops),
            "completed": len(completed),
            "total_volume_m3": round(sum(o.volume_m3 for o in completed), 1),
            "total_energy_kwh": round(sum(o.energy_kwh for o in completed), 1),
            "avg_predicted_risk": round(
                sum(o.predicted_leak_risk for o in ops) / len(ops), 4) if ops else 0.0,
        },
        "fleet": _fleet_snapshot(session),
    }


def _fleet_snapshot(session: Session) -> dict:
    tanks = session.exec(select(Tank)).all()
    status = Counter(t.status.value for t in tanks)
    return {"tanks": len(tanks), "by_status": dict(status)}


def parameter_trend(session: Session, tank_id: int, parameter: str, *, hours: int = 24,
                    buckets: int = 120) -> dict:
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    rows = session.exec(
        select(Reading).where(Reading.tank_id == tank_id, Reading.ts >= since)
        .order_by(Reading.ts)
    ).all()
    if not rows:
        return {"tank_id": tank_id, "parameter": parameter, "points": []}
    step = max(1, len(rows) // buckets)
    points = [
        {"ts": r.ts.isoformat(), "value": round(getattr(r, parameter, 0.0), 4)}
        for r in rows[::step]
    ]
    vals = [p["value"] for p in points]
    return {
        "tank_id": tank_id, "parameter": parameter, "hours": hours,
        "min": min(vals), "max": max(vals), "avg": round(sum(vals) / len(vals), 4),
        "points": points,
    }


def compliance_report(session: Session) -> dict:
    """FR-5.4 — API RP 2350 (overfill) + IEC 61511 (SIS) evidence summary."""
    tanks = session.exec(select(Tank)).all()
    overfill_alarms = session.exec(
        select(Alarm).where(Alarm.parameter == "level", Alarm.limit != None)  # noqa: E711
    ).all()
    esd_events = session.exec(
        select(EventRecord).where(EventRecord.title.like("ESD isolation%"))
    ).all()
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "api_rp_2350": {
            "tanks_with_overfill_limits": sum(1 for t in tanks if t.max_safe_level_pct < 100),
            "overfill_alarms_logged": len(overfill_alarms),
            "max_safe_level_policy_pct": [t.max_safe_level_pct for t in tanks[:20]],
        },
        "iec_61511": {
            "esd_activations": len(esd_events),
            "sis_interface": "Safety PLC (stub) — records ESD isolation commands as events",
            "two_person_rule": "enforced on CRITICAL alarms (FR-4.3)",
        },
        "audit_chain_intact": _audit_ok(session),
    }


def _audit_ok(session: Session) -> bool:
    from app.core.audit import verify_chain

    return verify_chain(session)
