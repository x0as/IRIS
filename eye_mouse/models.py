from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class EyeFeatures:
    vector: np.ndarray
    ear: float
    left_iris: tuple[float, float]
    right_iris: tuple[float, float]
    left_ear: float = 0.0
    right_ear: float = 0.0


@dataclass
class TrackingResult:
    features: Optional[EyeFeatures] = None
    face_detected: bool = False
    frame: Optional[np.ndarray] = None
    fps: float = 0.0


@dataclass
class GazePoint:
    x: float
    y: float
