from __future__ import annotations

from dataclasses import dataclass

from .models import GazePoint


@dataclass
class ExponentialSmoother:
    strength: float = 0.22
    _current: GazePoint | None = None

    def reset(self) -> None:
        self._current = None

    def update(self, point: GazePoint) -> GazePoint:
        alpha = max(0.01, min(1.0, self.strength))
        if self._current is None:
            self._current = point
        else:
            self._current = GazePoint(
                self._current.x + alpha * (point.x - self._current.x),
                self._current.y + alpha * (point.y - self._current.y),
            )
        return self._current
