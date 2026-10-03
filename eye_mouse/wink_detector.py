from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RightEyeDoubleBlink:
    threshold: float = 0.20
    minimum_duration: float = 0.06
    maximum_duration: float = 0.45
    window: float = 0.70
    cooldown: float = 0.80
    _closed_since: float | None = None
    _last_blink: float | None = None
    _cooldown_until: float = 0.0
    last_state: str = "OPEN"

    def update(self, right_ear: float, timestamp: float) -> bool:
        closed = right_ear < self.threshold
        self.last_state = "CLOSED" if closed else "OPEN"
        if closed:
            if self._closed_since is None:
                self._closed_since = timestamp
            return False
        if self._closed_since is None:
            return False
        duration = timestamp - self._closed_since
        self._closed_since = None
        if duration < self.minimum_duration or duration > self.maximum_duration or timestamp < self._cooldown_until:
            return False
        if self._last_blink is not None and timestamp - self._last_blink <= self.window:
            self._last_blink = None
            self._cooldown_until = timestamp + self.cooldown
            return True
        self._last_blink = timestamp
        return False

    def expire(self, timestamp: float) -> None:
        if self._last_blink is not None and timestamp - self._last_blink > self.window:
            self._last_blink = None