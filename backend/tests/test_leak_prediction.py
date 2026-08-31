from datetime import datetime, timedelta, timezone

from app.models.reading import Reading
from app.models.tank import Tank
from app.services import leak_prediction


def _inject(session, tank_id, minutes=60, leak=True):
    now = datetime.now(timezone.utc)
    for m in range(minutes, 0, -1):
        k = (minutes - m) / minutes
        session.add(Reading(
            tank_id=tank_id, ts=now - timedelta(minutes=m), source="test",
            level=50, temperature=25, pressure=1.6 - (0.4 * k if leak else 0),
            density=0.8,
            flammable_gas_ppm=12 + (90 * k if leak else 0),
            h2s_ppm=0.5 + (6 * k if leak else 0),
            vibration_mm_s=1.2 + (4 * k if leak else 0),
            corrosion_rate_mm_year=0.03,
            acoustic_db=42 + (25 * k if leak else 0),
            acoustic_leak_band_ratio=0.05 + (0.5 * k if leak else 0),
            leak_event=1 if (leak and k > 0.5) else 0,
        ))
    session.commit()


def test_leak_scenario_scores_high(session, seeded):
    tank = session.exec(Tank.__table__.select()).first()
    tank = session.get(Tank, 1)
    _inject(session, 1, leak=True)
    pred = leak_prediction.predict_tank(session, tank)
    assert pred.probability > 0.7
    assert pred.contributions  # explainability present


def test_normal_scenario_scores_low(session, seeded):
    tank = session.get(Tank, 2)
    _inject(session, 2, leak=False)
    pred = leak_prediction.predict_tank(session, tank)
    assert pred.probability < 0.4
