"""Seed the database: demo users, a terminal of tanks + pipelines, thresholds,
and a short history of synthetic readings.

    python -m app.seed            # idempotent-ish (skips if users already exist)
    python -m app.seed --reset    # drop everything first
"""
from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, SQLModel, select

from app.core.security import hash_password
from app.database import engine, init_db
from app.models.operation import Operation, OperationKind, OperationState
from app.models.reading import Reading
from app.models.tank import Pipeline, Tank, TankStatus, Threshold
from app.models.user import Role, User

DEMO_PASSWORD = "demo1234"

DEMO_USERS = [
    ("operator", "Ali Operator", Role.OPERATOR),
    ("safety", "Sara Safety", Role.SAFETY_ENGINEER),
    ("opsmanager", "Omid Operations", Role.OPS_MANAGER),
    ("technician", "Taghi Technician", Role.TECHNICIAN),
    ("exec", "Elham Executive", Role.EXECUTIVE),
    ("admin", "System Admin", Role.ADMIN),
]

PRODUCTS = ["crude", "gasoline", "diesel", "naphtha", "lpg"]


def reset() -> None:
    SQLModel.metadata.drop_all(engine)
    init_db()


def seed_users(s: Session) -> None:
    if s.exec(select(User)).first():
        return
    for username, full_name, role in DEMO_USERS:
        s.add(User(
            username=username, full_name=full_name, role=role,
            email=f"{username}@inno.example",
            hashed_password=hash_password(DEMO_PASSWORD),
        ))
    s.commit()
    print(f"seeded {len(DEMO_USERS)} users (password: {DEMO_PASSWORD})")


def seed_tanks(s: Session, n: int = 12) -> list[Tank]:
    existing = s.exec(select(Tank)).all()
    if existing:
        return existing
    rng = random.Random(2350)
    tanks = []
    cols = 4
    for i in range(n):
        row, col = divmod(i, cols)
        t = Tank(
            code=f"TK-{101 + i}",
            name=f"Storage Tank {101 + i}",
            product=rng.choice(PRODUCTS),
            capacity_m3=rng.choice([5000, 10000, 20000, 30000]),
            max_safe_level_pct=90.0,
            critical_level_pct=95.0,
            diameter_m=rng.choice([18, 22, 28, 35]),
            map_x=round(0.12 + col * 0.24, 3),
            map_y=round(0.15 + row * 0.26, 3),
            zone=chr(ord("A") + row),
            status=TankStatus.GREEN,
        )
        s.add(t)
        tanks.append(t)
    s.commit()
    for t in tanks:
        s.refresh(t)

    # pipelines: connect neighbours in a grid (for the GNN graph, FR-2.8)
    pipes = 0
    for i, t in enumerate(tanks):
        for j in (i + 1, i + cols):
            if j < len(tanks):
                s.add(Pipeline(
                    code=f"PL-{t.code}-{tanks[j].code}",
                    from_tank_id=t.id, to_tank_id=tanks[j].id,
                    length_m=random.Random(i * 7 + j).uniform(40, 160),
                    diameter_mm=random.Random(i + j).choice([200, 300, 400]),
                ))
                pipes += 1
    s.commit()

    # default thresholds for a couple of parameters per tank
    for t in tanks:
        s.add(Threshold(tank_id=t.id, parameter="level", hi_warn=t.max_safe_level_pct,
                        hi_critical=t.critical_level_pct, unit="%"))
        s.add(Threshold(tank_id=t.id, parameter="flammable_gas_ppm", hi_warn=40,
                        hi_critical=80, unit="ppm"))
    s.commit()
    print(f"seeded {len(tanks)} tanks + {pipes} pipelines + thresholds")
    return tanks


def seed_operations(s: Session, tanks: list[Tank]) -> None:
    if s.exec(select(Operation)).first():
        return
    rng = random.Random(11)
    now = datetime.now(timezone.utc)
    for i in range(6):
        t = rng.choice(tanks)
        s.add(Operation(
            ref=f"ERP-{2000 + i}",
            tank_id=t.id,
            kind=rng.choice(list(OperationKind)),
            volume_m3=rng.choice([2000, 4000, 6000, 8000]),
            flow_rate_m3ph=rng.choice([250, 300, 400, 500]),
            priority=rng.randint(1, 5),
            earliest_start=now + timedelta(hours=rng.randint(0, 4)),
            due_by=now + timedelta(hours=rng.randint(8, 30)),
            state=OperationState.REQUESTED,
            meta={"origin": "seed"},
        ))
    s.commit()
    print("seeded 6 operations")


def seed_readings(s: Session, tanks: list[Tank], minutes: int = 180) -> None:
    if s.exec(select(Reading)).first():
        return
    rng = random.Random(7)
    now = datetime.now(timezone.utc)
    total = 0
    for t in tanks:
        base_level = rng.uniform(35, 75)
        for m in range(minutes, 0, -1):
            ts = now - timedelta(minutes=m)
            wobble = rng.gauss(0, 0.3)
            s.add(Reading(
                tank_id=t.id, ts=ts, source="seed",
                level=max(0, min(100, base_level + 4 * (0.5 - rng.random()) + wobble)),
                temperature=25 + rng.gauss(0, 1.2),
                pressure=1.6 + rng.gauss(0, 0.05),
                density=0.8 + rng.gauss(0, 0.005),
                flammable_gas_ppm=max(0, 12 + rng.gauss(0, 2)),
                h2s_ppm=max(0, 0.5 + rng.gauss(0, 0.15)),
                vibration_mm_s=max(0, 1.2 + rng.gauss(0, 0.25)),
                corrosion_rate_mm_year=0.03 + rng.gauss(0, 0.004),
                acoustic_db=42 + rng.gauss(0, 1.0),
                acoustic_leak_band_ratio=max(0, 0.05 + rng.gauss(0, 0.01)),
                leak_event=0,
            ))
            total += 1
        s.commit()
    print(f"seeded {total} readings ({minutes} min history for {len(tanks)} tanks)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true")
    ap.add_argument("--no-readings", action="store_true")
    args = ap.parse_args()

    if args.reset:
        reset()
        print("database reset")
    else:
        init_db()

    with Session(engine) as s:
        seed_users(s)
        tanks = seed_tanks(s)
        seed_operations(s, tanks)
        if not args.no_readings:
            seed_readings(s, tanks)

    print("\nnext:")
    print("  uvicorn app.main:app --reload")
    print("  python -m app.ml.train      # train the baseline leak model")


if __name__ == "__main__":
    main()
