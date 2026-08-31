"""Window → feature vector for the leak models (shared by baseline + training)."""
from __future__ import annotations

import numpy as np

FEATURE_NAMES = [
    "pressure_slope", "pressure_last",
    "gas_slope", "gas_last", "gas_max",
    "h2s_slope", "h2s_last",
    "vibration_slope", "vibration_last",
    "level_slope",
    "temperature_slope",
    "acoustic_band_last", "acoustic_band_slope",
    "corrosion_last",
]


def _slope(a: np.ndarray) -> float:
    if len(a) < 3:
        return 0.0
    x = np.arange(len(a))
    return float(np.polyfit(x, a, 1)[0])


def window_features(window: list[dict]) -> np.ndarray:
    """window: list of reading dicts, oldest→newest."""
    if not window:
        return np.zeros(len(FEATURE_NAMES))
    w = window[-40:]

    def col(k: str) -> np.ndarray:
        return np.array([float(r.get(k, 0.0) or 0.0) for r in w])

    press, gas, h2s = col("pressure"), col("flammable_gas_ppm"), col("h2s_ppm")
    vib, lvl, temp = col("vibration_mm_s"), col("level"), col("temperature")
    band, corr = col("acoustic_leak_band_ratio"), col("corrosion_rate_mm_year")

    return np.array([
        _slope(press), press[-1],
        _slope(gas), gas[-1], gas.max(),
        _slope(h2s), h2s[-1],
        _slope(vib), vib[-1],
        _slope(lvl),
        _slope(temp),
        band[-1], _slope(band),
        corr[-1],
    ])
