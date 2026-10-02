from __future__ import annotations

from dataclasses import dataclass
from collections import deque

import numpy as np

from .models import GazePoint


@dataclass
class ExponentialSmoother:
    strength: float = 0.12
    window_size: int = 5
    deadband: float = 2.5
    _current: GazePoint | None = None
    _history: deque[GazePoint] | None = None

    def __post_init__(self) -> None:
        self._history = deque(maxlen=max(3, self.window_size))

    def reset(self) -> None:
        self._current = None
        if self._history is not None:
            self._history.clear()

    def update(self, point: GazePoint) -> GazePoint:
        if self._history is None:
            self._history = deque(maxlen=max(3, self.window_size))
        self._history.append(point)
        filtered = GazePoint(
            float(np.median([item.x for item in self._history])),
            float(np.median([item.y for item in self._history])),
        )
        alpha = max(0.01, min(1.0, self.strength))
        if self._current is None:
            self._current = filtered
        else:
            distance = ((filtered.x - self._current.x) ** 2 + (filtered.y - self._current.y) ** 2) ** 0.5
            if distance <= self.deadband:
                return self._current
            self._current = GazePoint(
                self._current.x + alpha * (filtered.x - self._current.x),
                self._current.y + alpha * (filtered.y - self._current.y),
            )
        return self._current
