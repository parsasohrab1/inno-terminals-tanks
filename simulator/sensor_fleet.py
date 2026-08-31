"""Synthetic IoT sensor fleet — stands in for physical ATEX sensors + gateways.

Each tank has a stateful sensor model producing autocorrelated readings. Leak
scenarios can be injected on demand; acoustic/vibration signatures move before
process parameters (patentable feature #4 rationale).
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field


@dataclass
class TankSensor:
    tank_code: str
    seed: int = 0
    level: float = 50.0
    temperature: float = 25.0
    pressure: float = 1.6
    density: float = 0.8
    flammable_gas_ppm: float = 12.0
    h2s_ppm: float = 0.5
    vibration_mm_s: float = 1.2
    corrosion_rate_mm_year: float = 0.03
    acoustic_db: float = 42.0
    acoustic_leak_band_ratio: float = 0.05

    _t: int = 0
    _leak_t: int = -1
    _leak_len: int = 0
    _leak_orifice: float = 0.0
    _rng: random.Random = field(default_factory=random.Random)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)
        self.level = self._rng.uniform(30, 78)

    def inject_leak(self, duration: int = 90, orifice: float | None = None) -> None:
        self._leak_t = 0
        self._leak_len = duration
        self._leak_orifice = orifice if orifice is not None else self._rng.uniform(0.6, 1.0)

    @property
    def leaking(self) -> bool:
        return 0 <= self._leak_t < self._leak_len

    def _ou(self, value: float, target: float, theta: float, sigma: float) -> float:
        return value + theta * (target - value) + self._rng.gauss(0, sigma)

    def step(self) -> dict:
        self._t += 1
        p = self._t
        self.temperature = self._ou(self.temperature, 25 + 4 * math.sin(p / 120), 0.05, 0.15)
        self.pressure = self._ou(self.pressure, 1.6, 0.05, 0.01)
        self.density = self._ou(self.density, 0.8, 0.03, 0.002)
        self.flammable_gas_ppm = self._ou(self.flammable_gas_ppm, 12, 0.1, 0.8)
        self.h2s_ppm = max(0.0, self._ou(self.h2s_ppm, 0.5, 0.1, 0.1))
        self.vibration_mm_s = max(0.0, self._ou(self.vibration_mm_s, 1.2, 0.08, 0.15))
        self.corrosion_rate_mm_year = max(0.0, self._ou(self.corrosion_rate_mm_year, 0.03, 0.02, 0.003))
        self.acoustic_db = self._ou(self.acoustic_db, 42, 0.1, 1.0)
        self.acoustic_leak_band_ratio = max(0.0, self._ou(self.acoustic_leak_band_ratio, 0.05, 0.1, 0.008))
        self.level = min(100.0, max(0.0, self._ou(self.level, self.level, 0.01, 0.05)))

        leak_event = 0
        if self.leaking:
            leak_event = 1
            k = self._leak_t / max(self._leak_len, 1)          # 0 -> 1 over the leak
            o = self._leak_orifice
            # acoustic + vibration respond first and strongly (feature #4)
            self.acoustic_leak_band_ratio = min(1.0, 0.05 + (0.55 * o) * min(1.0, k * 4))
            self.acoustic_db = 42 + (22 * o) * min(1.0, k * 4) + self._rng.gauss(0, 0.8)
            self.vibration_mm_s = 1.2 + (3.5 * o) * min(1.0, k * 3) + self._rng.gauss(0, 0.2)
            # process parameters lag by ~25% of the leak, then ramp hard
            lag = max(0.0, (k - 0.25) / 0.75)
            self.flammable_gas_ppm = 12 + (75 * o) * lag + self._rng.gauss(0, 1.5)
            self.h2s_ppm = 0.5 + (6 * o) * lag
            self.pressure = 1.6 - (0.35 * o) * lag
            self.level = max(0.0, self.level - 0.02 * o)
            self._leak_t += 1
            if self._leak_t >= self._leak_len:
                self._leak_len = 0
                self._leak_t = -1

        return {
            "tank_code": self.tank_code,
            "level": round(self.level, 3),
            "temperature": round(self.temperature, 3),
            "pressure": round(self.pressure, 4),
            "density": round(self.density, 4),
            "flammable_gas_ppm": round(max(self.flammable_gas_ppm, 0), 3),
            "h2s_ppm": round(self.h2s_ppm, 3),
            "vibration_mm_s": round(self.vibration_mm_s, 3),
            "corrosion_rate_mm_year": round(self.corrosion_rate_mm_year, 4),
            "acoustic_db": round(self.acoustic_db, 2),
            "acoustic_leak_band_ratio": round(self.acoustic_leak_band_ratio, 4),
            "leak_event": leak_event,
            "source": "sensor",
        }
