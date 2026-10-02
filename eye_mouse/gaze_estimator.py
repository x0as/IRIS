from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .models import GazePoint


class GazeEstimator:
    """Maps calibrated feature vectors to screen coordinates with quadratic terms."""

    def __init__(self, screen_size: tuple[int, int]) -> None:
        self.screen_width, self.screen_height = screen_size
        self._coefficients: np.ndarray | None = None
        self.feature_count: int | None = None

    @staticmethod
    def _design_matrix(features: np.ndarray) -> np.ndarray:
        features = np.asarray(features, dtype=float)
        if features.ndim == 1:
            features = features[None, :]
        return np.concatenate((np.ones((len(features), 1)), features, features**2), axis=1)

    def fit(self, features: list[np.ndarray], points: list[GazePoint]) -> float:
        if len(features) < 3 or len(features) != len(points):
            raise ValueError("At least three matching calibration samples are required")
        matrix = self._design_matrix(np.asarray(features))
        targets = np.array([[point.x, point.y] for point in points], dtype=float)
        self._coefficients, *_ = np.linalg.lstsq(matrix, targets, rcond=None)
        predicted = matrix @ self._coefficients
        return float(np.mean(np.linalg.norm(predicted - targets, axis=1)))

    def predict(self, features: np.ndarray) -> GazePoint:
        if self._coefficients is None:
            raise RuntimeError("Gaze estimator has not been calibrated")
        result = self._design_matrix(features) @ self._coefficients
        return GazePoint(
            float(np.clip(result[0, 0], 0, self.screen_width - 1)),
            float(np.clip(result[0, 1], 0, self.screen_height - 1)),
        )

    def save(self, path: Path) -> None:
        if self._coefficients is None:
            raise RuntimeError("Cannot save an uncalibrated estimator")
        payload = {"screen_size": [self.screen_width, self.screen_height], "coefficients": self._coefficients.tolist()}
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path, screen_size: tuple[int, int]) -> "GazeEstimator":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if tuple(payload["screen_size"]) != tuple(screen_size):
            raise ValueError("Saved calibration belongs to a different screen size")
        estimator = cls(screen_size)
        estimator._coefficients = np.asarray(payload["coefficients"], dtype=float)
        return estimator
