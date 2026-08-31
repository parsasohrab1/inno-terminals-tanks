"""Baseline leak model: IsolationForest anomaly score + gradient-boosted
classifier over engineered window features (FR-2.1).

Explainability (FR-2.4): permutation feature-importance around the current
sample gives a SHAP-lite contribution breakdown.
"""
from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler

from app.config import settings
from app.ml.features import FEATURE_NAMES

_MODEL_PATH = settings.model_store_dir / "leak_baseline.joblib"


class LeakBaselineModel:
    def __init__(self) -> None:
        self.scaler = StandardScaler()
        self.iforest = IsolationForest(n_estimators=200, contamination=0.05, random_state=42)
        self.clf = GradientBoostingClassifier(n_estimators=250, max_depth=4, random_state=42)
        self.decision_threshold = 0.5
        self.trained = False
        self.metrics: dict = {}

    # --- training ---
    def fit(self, X: np.ndarray, y: np.ndarray) -> dict:
        Xs = self.scaler.fit_transform(X)
        self.iforest.fit(Xs)
        # upweight the (rarer, safety-critical) leak class to push recall toward
        # the FR-2.6 target of 0.95 while keeping the false-alarm rate < 5%.
        pos = max(int(y.sum()), 1)
        neg = max(int((y == 0).sum()), 1)
        w = np.where(y == 1, neg / pos * 1.4, 1.0)
        self.clf.fit(Xs, y, sample_weight=w)
        self.trained = True

        from sklearn.metrics import precision_score, recall_score

        proba = self.clf.predict_proba(Xs)[:, 1]
        # pick the lowest threshold that keeps false-alarm rate <= 5%
        self.decision_threshold = 0.5
        for thr in np.arange(0.15, 0.85, 0.05):
            p = (proba >= thr).astype(int)
            far = ((p == 1) & (y == 0)).sum() / neg
            rec = recall_score(y, p, zero_division=0)
            if far <= 0.05 and rec >= 0.95:
                self.decision_threshold = float(thr)
                break
            if rec >= 0.95:
                self.decision_threshold = float(thr)
        pred = (proba >= self.decision_threshold).astype(int)
        self.metrics = {
            "n_samples": int(len(y)),
            "positives": int(y.sum()),
            "recall": round(float(recall_score(y, pred, zero_division=0)), 3),
            "precision": round(float(precision_score(y, pred, zero_division=0)), 3),
            "false_alarm_rate": round(float(((pred == 1) & (y == 0)).sum() / max((y == 0).sum(), 1)), 3),
            "decision_threshold": round(self.decision_threshold, 3),
        }
        return self.metrics

    def save(self, path: Path | None = None) -> Path:
        path = path or _MODEL_PATH
        joblib.dump(self, path)
        return path

    @classmethod
    def load(cls, path: Path | None = None) -> "LeakBaselineModel | None":
        path = path or _MODEL_PATH
        if not path.exists():
            return None
        try:
            return joblib.load(path)
        except Exception:  # noqa: BLE001
            return None

    # --- inference ---
    def predict_one(self, feats: np.ndarray) -> dict:
        if not self.trained:
            return self._heuristic(feats)
        Xs = self.scaler.transform(feats.reshape(1, -1))
        proba = float(self.clf.predict_proba(Xs)[0, 1])
        # calibrate so the tuned decision threshold maps to 0.85 (the alarm line)
        thr = self.decision_threshold or 0.5
        if proba <= thr:
            proba_cal = 0.85 * (proba / thr)
        else:
            proba_cal = 0.85 + 0.15 * ((proba - thr) / (1 - thr))
        raw = float(-self.iforest.score_samples(Xs)[0])  # higher = more anomalous
        anomaly = float(np.clip((raw - 0.4) / 0.4, 0, 1))
        prob = float(np.clip(0.8 * proba_cal + 0.2 * anomaly, 0, 1))
        return {
            "probability": prob,
            "anomaly_score": anomaly,
            "contributions": self._contributions(Xs, feats),
            "model_name": "baseline",
        }

    def _contributions(self, Xs: np.ndarray, feats: np.ndarray) -> dict:
        base = float(self.clf.predict_proba(Xs)[0, 1])
        out: dict[str, float] = {}
        for i, name in enumerate(FEATURE_NAMES):
            perturbed = Xs.copy()
            perturbed[0, i] = 0.0
            delta = base - float(self.clf.predict_proba(perturbed)[0, 1])
            out[name] = round(delta, 4)
        total = sum(abs(v) for v in out.values()) or 1.0
        return dict(sorted(
            ((k, round(v / total, 4)) for k, v in out.items()),
            key=lambda kv: -abs(kv[1]),
        )[:6])

    @staticmethod
    def _heuristic(feats: np.ndarray) -> dict:
        f = dict(zip(FEATURE_NAMES, feats))
        score = (
            0.35 * np.clip(f["gas_slope"] / 2.0, 0, 1)
            + 0.25 * np.clip(-f["pressure_slope"] / 0.02, 0, 1)
            + 0.20 * np.clip(f["vibration_slope"] / 0.2, 0, 1)
            + 0.20 * np.clip(f["acoustic_band_last"] / 0.4, 0, 1)
        )
        return {
            "probability": float(np.clip(score, 0, 1)),
            "anomaly_score": float(np.clip(score, 0, 1)),
            "contributions": {
                "gas_slope": 0.35, "pressure_slope": 0.25,
                "vibration_slope": 0.20, "acoustic_band_last": 0.20,
            },
            "model_name": "baseline-heuristic",
        }


_cache: dict[str, LeakBaselineModel] = {}


def get_model() -> LeakBaselineModel:
    if "m" not in _cache:
        _cache["m"] = LeakBaselineModel.load() or LeakBaselineModel()
    return _cache["m"]


def reload_model() -> None:
    _cache.pop("m", None)
