"""OPEN synthetic sensor-data generator (SRS appendix 5.1, refined).

This is the non-proprietary baseline used for model training and demos when the
IP vault is locked. The proprietary digital twin (feature #3) supersedes it when
available.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def generate_synthetic_tank_data(
    num_tanks: int = 10,
    num_days: int = 7,
    sampling_rate_hz: float = 1 / 60,   # 1 sample/minute keeps demo data small
    leak_probability: float = 0.0006,
    seed: int = 42,
) -> pd.DataFrame:
    """Refined version of the SRS appendix 5.1 generator.

    Adds acoustic leak-band features (FR-1.7) and a leak precursor pattern where
    acoustic/vibration move before process parameters.
    """
    rng = np.random.default_rng(seed)
    start = pd.Timestamp.utcnow().tz_localize(None) - pd.Timedelta(days=num_days)
    n = max(1, int(num_days * 24 * 3600 * sampling_rate_hz))
    freq = pd.Timedelta(seconds=1 / sampling_rate_hz)
    ts = pd.date_range(start=start, periods=n, freq=freq)

    frames = []
    for tank_id in range(1, num_tanks + 1):
        base = {
            "level": rng.uniform(20, 80), "temperature": rng.uniform(20, 35),
            "pressure": rng.uniform(1.0, 2.5), "density": rng.uniform(0.7, 0.9),
            "flammable_gas_ppm": rng.uniform(5, 20), "h2s_ppm": rng.uniform(0.1, 1.0),
            "vibration_mm_s": rng.uniform(0.5, 2.0), "corrosion_rate_mm_year": rng.uniform(0.01, 0.05),
            "acoustic_db": rng.uniform(38, 46),
        }
        lin = np.linspace
        level = base["level"] + 5 * np.sin(lin(0, 4 * np.pi, n)) + rng.normal(0, 0.2, n)
        temperature = base["temperature"] + 3 * np.sin(lin(0, 2 * np.pi, n)) + rng.normal(0, 0.5, n)
        pressure = base["pressure"] + 0.1 * np.cos(lin(0, 6 * np.pi, n)) + rng.normal(0, 0.02, n)
        density = base["density"] + 0.01 * np.sin(lin(0, 8 * np.pi, n)) + rng.normal(0, 0.005, n)
        gas = base["flammable_gas_ppm"] + 2 * rng.normal(0, 1, n)
        h2s = base["h2s_ppm"] + 0.1 * rng.normal(0, 0.2, n)
        vibration = base["vibration_mm_s"] + 0.2 * rng.normal(0, 0.5, n)
        corrosion = base["corrosion_rate_mm_year"] + 0.005 * rng.normal(0, 0.01, n)
        acoustic_db = base["acoustic_db"] + rng.normal(0, 1.0, n)
        acoustic_band = 0.05 + np.abs(rng.normal(0, 0.01, n))
        leak = np.zeros(n, dtype=int)

        i = 0
        while i < n:
            if rng.random() < leak_probability:
                dur = int(rng.integers(30, 180))
                end = min(i + dur, n)
                k = end - i
                leak[i:end] = 1
                ramp = lin(0, 1, k)
                acoustic_band[i:end] += ramp * 0.5 + rng.normal(0, 0.02, k)
                acoustic_db[i:end] += ramp * 16 + rng.normal(0, 1, k)
                vibration[i:end] += ramp * 3 + rng.normal(0, 0.3, k)
                glag = np.clip(lin(-0.4, 1, k), 0, 1)
                gas[i:end] += glag * 50 + rng.normal(0, 2, k)
                h2s[i:end] += glag * 5 + rng.normal(0, 0.5, k)
                pressure[i:end] -= glag * 0.3
                level[i:end] -= glag * 0.5
                i = end
            i += 1

        frames.append(pd.DataFrame({
            "timestamp": ts, "tank_id": tank_id,
            "level": np.clip(level, 0, 100),
            "temperature": np.clip(temperature, -10, 60),
            "pressure": np.clip(pressure, 0.5, 5.0),
            "density": np.clip(density, 0.5, 1.2),
            "flammable_gas_ppm": np.clip(gas, 0, 300),
            "h2s_ppm": np.clip(h2s, 0, 20),
            "vibration_mm_s": np.clip(vibration, 0, 15),
            "corrosion_rate_mm_year": np.clip(corrosion, 0, 0.5),
            "acoustic_db": np.clip(acoustic_db, 20, 120),
            "acoustic_leak_band_ratio": np.clip(acoustic_band, 0, 1),
            "leak_event": leak,
        }))

    df = pd.concat(frames, ignore_index=True).sort_values("timestamp")
    return df.reset_index(drop=True)


def open_synthetic_corpus(num_tanks: int = 8, num_days: int = 4) -> pd.DataFrame:
    df = generate_synthetic_tank_data(num_tanks=num_tanks, num_days=num_days)
    df = df.rename(columns={"timestamp": "t"})
    df["scenario"] = 0
    return df


if __name__ == "__main__":
    out = generate_synthetic_tank_data(num_tanks=10, num_days=7)
    print(f"rows: {len(out):,}  leaks: {int(out.leak_event.sum()):,}")
    out.to_csv("data/synthetic_tank_data.csv", index=False)
    print("wrote data/synthetic_tank_data.csv")
