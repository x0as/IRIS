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
        self._gesture_start_x: float | None = None
        self._gesture_start_time: float | None = None
        self._gesture_fingers: int | None = None
        self._last_gesture_time = 0.0
        self.last_gesture = "None"
        self._last_finger_count = -1
        self._last_scroll_y: float | None = None

    def update(self, x: float, y: float, pinching: bool, finger_count: int = 0) -> GazePoint:
        point = GazePoint(x * (self.screen_width - 1), y * (self.screen_height - 1))
        point = self.smoother.update(point)
        self.last_point = point
        self.mouse.move_to(point)
        now = time.monotonic()
        if pinching and not self._pinching and now - self._last_click >= 0.6 and self.mouse.enabled:
            pyautogui.click(button="left")
            self._last_click = now
        self._pinching = pinching
        self._update_pose_gestures(y, finger_count, now)
        self._update_swipe_gesture(x, finger_count, now)
        return point

    def _update_pose_gestures(self, y: float, finger_count: int, now: float) -> None:
        if not self.mouse.enabled:
            self._last_finger_count = finger_count
            self._last_scroll_y = y if finger_count == 2 else None
            return
        if finger_count == 0:
            if self._last_finger_count != 0 and now - self._last_click >= 0.6:
                pyautogui.click(button="left")
                self._last_click = now
                self.last_gesture = "fist click"
            self._last_scroll_y = None
        elif finger_count == 2:
            if self._last_scroll_y is not None:
                delta = self._last_scroll_y - y
                if abs(delta) >= 0.025:
                    pyautogui.scroll(max(-8, min(8, round(delta * 40))))
                    self.last_gesture = "2-finger scroll"
                    self._last_scroll_y = y
            else:
                self._last_scroll_y = y
        else:
            self._last_scroll_y = None
        self._last_finger_count = finger_count

    def _update_swipe_gesture(self, x: float, finger_count: int, now: float) -> None:
        if not self.mouse.enabled:
            self._gesture_start_x = x
            self._gesture_start_time = now
            self._gesture_fingers = finger_count
            return
        if finger_count not in (3, 4):
            self._gesture_start_x = None
            self._gesture_start_time = None
            self._gesture_fingers = None
            return
        if self._gesture_fingers != finger_count or self._gesture_start_x is None:
            self._gesture_fingers = finger_count
            self._gesture_start_x = x
            self._gesture_start_time = now
            return
        if now - self._last_gesture_time < 1.0 or self._gesture_start_time is None:
            return
        elapsed = now - self._gesture_start_time
        distance = x - self._gesture_start_x
        if elapsed <= 0.15 or abs(distance) < 0.18:
            return
        direction = "right" if distance > 0 else "left"
        if finger_count == 4:
            pyautogui.hotkey("win", "ctrl", direction)
            self.last_gesture = f"4-finger desktop {direction}"
        else:
            pyautogui.hotkey("alt", "tab" if direction == "right" else "shift", "tab" if direction == "left" else "tab")
            self.last_gesture = f"3-finger app switch {direction}"
        self._last_gesture_time = now
        self._gesture_start_x = x
        self._gesture_start_time = now
