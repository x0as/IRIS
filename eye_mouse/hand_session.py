from __future__ import annotations

import time

import pyautogui

from .models import GazePoint
from .mouse_controller import MouseController
from .smoothing import ExponentialSmoother


class HandSession:
    def __init__(self, screen_size: tuple[int, int], smoothing: float, mouse_enabled: bool) -> None:
        self.screen_width, self.screen_height = screen_size
        self.smoother = ExponentialSmoother(smoothing)
        self.mouse = MouseController(mouse_enabled)
        self.last_point: GazePoint | None = None
        self._pinching = False
        self._last_click = 0.0

    def update(self, x: float, y: float, pinching: bool) -> GazePoint:
        point = self.smoother.update(GazePoint(x * (self.screen_width - 1), y * (self.screen_height - 1)))
        self.last_point = point
        self.mouse.move_to(point)
        now = time.monotonic()
        if pinching and not self._pinching and now - self._last_click >= 0.6 and self.mouse.enabled:
            pyautogui.click(button="left")
            self._last_click = now
        self._pinching = pinching
        return point
