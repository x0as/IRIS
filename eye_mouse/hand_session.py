from __future__ import annotations

import time

import pyautogui

from .models import GazePoint
from .mouse_controller import MouseController
from .smoothing import ExponentialSmoother


class HandSession:
    def __init__(self, screen_size: tuple[int, int], smoothing: float, mouse_enabled: bool, gesture_preview: bool = False) -> None:
        self.screen_width, self.screen_height = screen_size
        self.smoother = ExponentialSmoother(smoothing)
        self.mouse = MouseController(mouse_enabled)
        self.gesture_preview = gesture_preview
        self.last_point: GazePoint | None = None
        self._pinching = False
        self._middle_pinching = False
        self._pinch_started_at: float | None = None
        self._last_click = 0.0
        self._gesture_start_x: float | None = None
        self._gesture_start_time: float | None = None
        self._gesture_fingers: int | None = None
        self.last_gesture = "None"
        self._last_action_time = 0.0
        self._last_finger_count = -1
        self._last_scroll_y: float | None = None
        self._alt_switch_until = 0.0

    def update(self, x: float, y: float, pinching: bool, finger_count: int = 0, fingers: tuple[bool, ...] | None = None, palm_y: float | None = None, middle_pinching: bool = False, middle_near: bool = False, index_near: bool = False) -> GazePoint:
        now = time.monotonic()
        self._release_alt_switch(now)
        if fingers is None:
            fingers = (False, finger_count == 1, finger_count == 2, finger_count == 3, finger_count == 4)
        thumb_outward = fingers[0]
        index_middle = thumb_outward and fingers[1] and fingers[2] and not fingers[3] and not fingers[4]
        middle_ring = thumb_outward and fingers[2] and fingers[3] and not fingers[1] and not fingers[4]
        only_index = thumb_outward and fingers[1] and not any(fingers[2:])
        candidate = self.smoother.update(GazePoint(x * (self.screen_width - 1), y * (self.screen_height - 1)))
        pinch_freeze = pinching or index_near or (not pinching and self._pinching)
        point = self.last_point if (index_middle or middle_ring or pinch_freeze) and self.last_point is not None else candidate
        self.last_point = point
        if not pinch_freeze and not index_middle and not middle_ring and only_index:
            self.mouse.move_to(point)
        if pinching and not self._pinching:
            self._set_gesture("LEFT CLICK READY", now)
        elif not pinching and self._pinching:
            if now - self._last_click >= 0.6:
                if self.mouse.enabled:
                    pyautogui.click(button="left")
                self._last_click = now
                self._set_gesture("LEFT CLICK", now)
        self._pinching = pinching
        self._middle_pinching = middle_pinching
        scroll_direction = "down" if index_middle else "up" if middle_ring else None
        self._update_pose_gestures(y if palm_y is None else palm_y, finger_count, now, scroll_direction)
        self._update_swipe_gesture(x, finger_count, now, thumb_outward)
        return point

    def active_gesture(self, now: float | None = None) -> str | None:
        timestamp = time.monotonic() if now is None else now
        if timestamp - self._last_action_time <= 0.8:
            return self.last_gesture
        return None

    def _update_pose_gestures(self, y: float, finger_count: int, now: float, scroll_direction: str | None = None) -> None:
        if not self.mouse.enabled and not self.gesture_preview:
            self._last_finger_count = finger_count
            self._last_scroll_y = y if scroll_direction else None
            return
        if finger_count == 0:
            if self._last_finger_count != 0 and now - self._last_click >= 0.6:
                if self.mouse.enabled:
                    pyautogui.click(button="left")
                self._last_click = now
                self._set_gesture("fist click", now)
            self._last_scroll_y = None
        elif scroll_direction:
            if self._last_scroll_y is not None:
                delta = self._last_scroll_y - y
                if abs(delta) >= 0.012:
                    if self.mouse.enabled:
                        amount = abs(round(delta * 60))
                        pyautogui.scroll(amount if scroll_direction == "up" else -amount)
                    self._set_gesture(f"SCROLL {scroll_direction.upper()}", now)
                    self._last_scroll_y = y
            else:
                self._last_scroll_y = y
        else:
            self._last_scroll_y = None
        self._last_finger_count = finger_count

    def cancel_actions(self) -> None:
        self._pinching = False
        self.mouse.enabled = False
        self._release_alt_switch(time.monotonic(), force=True)

    def _release_alt_switch(self, now: float, force: bool = False) -> None:
        if self._alt_switch_until and (force or now >= self._alt_switch_until):
            if self.mouse.enabled:
                pyautogui.keyUp("alt")
            self._alt_switch_until = 0.0

    def _update_swipe_gesture(self, x: float, finger_count: int, now: float, thumb_outward: bool = True) -> None:
        if not thumb_outward:
            self._gesture_start_x = None
            self._gesture_start_time = None
            self._gesture_fingers = None
            return
        if not self.mouse.enabled:
            self._gesture_start_x = x
            self._gesture_start_time = now
            self._gesture_fingers = finger_count
            return
        if finger_count not in (3, 5):
            self._gesture_start_x = None
            self._gesture_start_time = None
            self._gesture_fingers = None
            return
        if self._gesture_fingers != finger_count or self._gesture_start_x is None:
            self._gesture_fingers = finger_count
            self._gesture_start_x = x
            self._gesture_start_time = now
            return
        if now - self._last_action_time < 1.0 or self._gesture_start_time is None:
            return
        elapsed = now - self._gesture_start_time
        distance = x - self._gesture_start_x
        if elapsed <= 0.15 or abs(distance) < 0.18:
            return
        direction = "right" if distance > 0 else "left"
        if finger_count == 5:
            if self.mouse.enabled:
                desktop_direction = "left" if direction == "right" else "right"
                pyautogui.hotkey("win", "ctrl", desktop_direction)
            self._set_gesture(f"open-palm desktop {'left' if direction == 'right' else 'right'}", now)
        else:
            if self.mouse.enabled:
                pyautogui.keyDown("alt")
                if direction == "left":
                    pyautogui.keyDown("shift")
                    pyautogui.press("tab")
                    pyautogui.keyUp("shift")
                else:
                    pyautogui.press("tab")
                self._alt_switch_until = now + 0.8
            self._set_gesture(f"3-finger app switch {direction}", now)
        self._last_gesture_time = now
        self._gesture_start_x = x
        self._gesture_start_time = now

    def _set_gesture(self, gesture: str, timestamp: float) -> None:
        self.last_gesture = gesture
        self._last_action_time = timestamp
