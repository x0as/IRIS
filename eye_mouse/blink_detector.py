from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class BlinkAction(str, Enum):
    LEFT_CLICK = "left_click"
    RIGHT_CLICK = "right_click"


@dataclass
class BlinkDetector:
    ear_threshold: float = 0.20
    min_duration: float = 0.08
    long_duration: float = 0.55
    max_duration: float = 1.8
    double_window: float = 0.65
    cooldown: float = 0.8
    _closed_since: float | None = None
    _last_blink: float | None = None
    _cooldown_until: float = 0.0
    _waiting_for_open: bool = False
    _pending_short_blink: bool = False
    last_state: str = "OPEN"

    def reset(self) -> None:
        self._closed_since = None
        self._last_blink = None
        self._cooldown_until = 0.0
        self._waiting_for_open = False
        self._pending_short_blink = False
        self.last_state = "OPEN"

    def update(self, ear: float, timestamp: float) -> BlinkAction | None:
        closed = ear < self.ear_threshold
        self.last_state = "CLOSED" if closed else "OPEN"
        if closed:
            if self._closed_since is None and not self._waiting_for_open:
                self._closed_since = timestamp
            return None

        if self._closed_since is None:
            return None
        duration = timestamp - self._closed_since
        self._closed_since = None
        self._waiting_for_open = False
        if duration < self.min_duration or duration > self.max_duration:
            return None
        if timestamp < self._cooldown_until:
            return None

        if duration >= self.long_duration:
            self._pending_short_blink = False
            self._cooldown_until = timestamp + self.cooldown
            return BlinkAction.RIGHT_CLICK

        if self._pending_short_blink and self._last_blink is not None and timestamp - self._last_blink <= self.double_window:
            self._pending_short_blink = False
            self._last_blink = None
            self._cooldown_until = timestamp + self.cooldown
            return BlinkAction.LEFT_CLICK

        self._pending_short_blink = True
        self._last_blink = timestamp
        return None

    def expire_pending(self, timestamp: float) -> None:
        if self._last_blink is not None and timestamp - self._last_blink > self.double_window:
            self._pending_short_blink = False
            self._last_blink = None
