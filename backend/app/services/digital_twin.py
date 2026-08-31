"""Digital twin — live model + What-If leak simulation (SRS 5.2, FR-2.7).

Open baseline: a lumped-parameter tank model (mass balance + first-order
dynamics). When the vault is unlocked, feature #3's physics-informed twin
provides higher-fidelity, labelled leak scenarios for training and drills.
"""
from __future__ import annotations

from sqlmodel import Session, select

from app import secure
from app.models.reading import Reading
from app.models.tank import Tank


def _latest(session: Session, tank_id: int) -> Reading | None:
    return session.exec(
        select(Reading).where(Reading.tank_id == tank_id).order_by(Reading.ts.desc())
    ).first()


def twin_state(session: Session, tank: Tank) -> dict:
    r = _latest(session, tank.id)
    fill = (r.level / 100.0) if r else 0.5
    return {
        "tank_id": tank.id,
        "code": tank.code,
        "product": tank.product,
        "fill_fraction": round(fill, 4),
        "volume_m3": round(fill * tank.capacity_m3, 1),
        "ullage_m3": round((1 - fill) * tank.capacity_m3, 1),
        "surface_pressure_bar": r.pressure if r else 1.6,
        "skin_temperature_c": r.temperature if r else 25.0,
        "fidelity": "high" if secure.load("twin_leak_sim") else "lumped-parameter",
        "updated_from_reading": r.ts.isoformat() if r else None,
    }


def simulate(session: Session, tank: Tank, *, minutes: int = 120, leak: bool = True,
             seed: int | None = None) -> dict:
    """FR-2.9 — produce a labelled scenario trace for training / operator drills."""
    prop = secure.load("twin_leak_sim")
    spec = {
        "id": tank.id, "product": tank.product, "capacity_m3": tank.capacity_m3,
        "max_safe_level_pct": tank.max_safe_level_pct,
        "level_pct": (_latest(session, tank.id).level if _latest(session, tank.id) else 55.0),
    }
    if prop is not None:
        rows = prop.simulate_scenario(spec, minutes=minutes, leak=leak, seed=seed)
        engine = "proprietary-physics-twin"
    else:
        rows = _lumped_sim(spec, minutes=minutes, leak=leak, seed=seed)
        engine = "lumped-parameter"
    leak_onset = next((row["minute"] for row in rows if row["leak_event"]), None)
    return {
        "tank": tank.code, "engine": engine, "minutes": minutes,
        "leak": leak, "leak_onset_minute": leak_onset,
        "trace": rows,
    }


def _lumped_sim(spec: dict, *, minutes: int, leak: bool, seed: int | None) -> list[dict]:
    import numpy as np

    rng = np.random.default_rng(seed)
    n = minutes
    level = float(spec.get("level_pct", 55.0))
    rows = []
    onset = int(n * rng.uniform(0.35, 0.65)) if leak else n + 1
    gas, press, vib, band = 12.0, 1.6, 1.2, 0.05
    for m in range(n):
        drift = rng.normal(0, 0.3)
        if m >= onset:
            k = (m - onset) / max(n - onset, 1)
            gas += 1.5 + rng.normal(0, 0.5)
            press -= 0.01
            vib += 0.05
            band = min(1.0, band + 0.01)
            level -= 0.02
        rows.append({
            "minute": m, "level": round(level + drift, 3),
            "temperature": round(25 + 3 * np.sin(m / 30) + rng.normal(0, 0.3), 3),
            "pressure": round(press + rng.normal(0, 0.01), 4),
            "density": round(0.8 + rng.normal(0, 0.002), 4),
            "flammable_gas_ppm": round(max(gas + rng.normal(0, 1), 0), 3),
            "h2s_ppm": round(max(0.5 + (gas - 12) * 0.08, 0), 3),
            "vibration_mm_s": round(max(vib + rng.normal(0, 0.1), 0), 3),
            "corrosion_rate_mm_year": 0.03,
            "acoustic_db": round(42 + (band - 0.05) * 120 + rng.normal(0, 1), 2),
            "acoustic_leak_band_ratio": round(band, 4),
            "leak_event": int(m >= onset),
        })
    return rows
