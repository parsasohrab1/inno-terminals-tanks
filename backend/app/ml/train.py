"""Train the baseline leak model (FR-2.2 periodic retraining).

Training data comes from the proprietary digital-twin corpus (feature #3) when
the IP vault is unlocked, otherwise from an open synthetic generator.

    python -m app.ml.train                 # auto source
    python -m app.ml.train --csv data/synthetic_tank_data.csv
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from app import secure
from app.ml.features import window_features
from app.ml.model import LeakBaselineModel, reload_model
from app.synthetic import open_synthetic_corpus


def _windows_from_frame(df: pd.DataFrame, win: int = 40, stride: int = 10):
    X, y = [], []
    for _, g in df.groupby(["tank_id", df.get("scenario", 0)]):
        g = g.sort_values(g.columns[0])
        rows = g.to_dict("records")
        for i in range(win, len(rows), stride):
            w = rows[i - win : i]
            X.append(window_features(w))
            # positive if a leak occurs within the next 30 samples (≈30 min horizon)
            future = rows[i : i + 30]
            y.append(int(any(r.get("leak_event", 0) for r in future)))
    return np.array(X), np.array(y)


def load_corpus(csv: str | None) -> pd.DataFrame:
    if csv:
        return pd.read_csv(csv)
    twin = secure.load("twin_leak_sim")
    if twin is not None:
        from app.database import engine
        from sqlmodel import Session, select
        from app.models.tank import Tank

        with Session(engine) as s:
            tanks = [
                {"id": t.id, "product": t.product, "capacity_m3": t.capacity_m3,
                 "max_safe_level_pct": t.max_safe_level_pct, "level_pct": 55.0}
                for t in s.exec(select(Tank)).all()
            ]
        if tanks:
            print(f"[train] using proprietary digital-twin corpus ({len(tanks)} tanks)")
            return pd.DataFrame(twin.generate_training_corpus(tanks, scenarios_per_tank=10, seed=7))
    print("[train] IP vault locked — using open synthetic corpus")
    return open_synthetic_corpus(num_tanks=8, num_days=4)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=None)
    args = ap.parse_args()

    df = load_corpus(args.csv)
    X, y = _windows_from_frame(df)
    if len(X) == 0 or y.sum() == 0:
        raise SystemExit("no usable training windows / no positive labels")

    model = LeakBaselineModel()
    metrics = model.fit(X, y)
    path = model.save()
    reload_model()
    print(f"[train] saved {path}")
    print(f"[train] metrics: {metrics}")
    if metrics["recall"] < 0.9:
        print("[train] WARNING: recall below FR-2.6 target (0.95)")


if __name__ == "__main__":
    main()
