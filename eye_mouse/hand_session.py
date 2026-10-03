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
        self._dragging = False
        self._alt_switch_until = 0.0

    def update(self, x: float, y: float, pinching: bool, finger_count: int = 0, fingers: tuple[bool, ...] | None = None, palm_y: float | None = None, middle_pinching: bool = False, middle_near: bool = False) -> GazePoint:
        now = time.monotonic()
        self._release_alt_switch(now)
        if fingers is None:
            fingers = (False, finger_count == 1, finger_count == 2, finger_count == 3, finger_count == 4)
        index_middle = fingers[1] and fingers[2] and not fingers[3] and not fingers[4]
        only_index = fingers[1] and not any(fingers[2:])
        candidate = self.smoother.update(GazePoint(x * (self.screen_width - 1), y * (self.screen_height - 1)))
        pinch_freeze = pinching
        point = self.last_point if (index_middle or (pinch_freeze and not self._dragging)) and self.last_point is not None else candidate
        self.last_point = point
        if self._dragging:
            self.mouse.move_to(point)
        elif not pinch_freeze and not index_middle and only_index:
            self.mouse.move_to(point)
        if pinching and not self._pinching:
            self._pinch_started_at = now
            self._set_gesture("LEFT CLICK READY", now)
        elif pinching and not self._dragging and self._pinch_started_at is not None and now - self._pinch_started_at >= 0.50:
            self._dragging = True
            self.mouse.press_left()
            self._set_gesture("DRAG START", now)
        elif not pinching and self._pinching:
            if self._dragging:
                self._dragging = False
                self.mouse.release_left()
                self._set_gesture("DRAG END", now)
            elif now - self._last_click >= 0.6:
                if self.mouse.enabled:
                    pyautogui.click(button="left")
                self._last_click = now
                self._set_gesture("LEFT CLICK", now)
            self._pinch_started_at = None
        elif pinching and self._dragging:
            self._set_gesture("DRAGGING", now)
        self._pinching = pinching
        self._middle_pinching = middle_pinching
        self._update_pose_gestures(y if palm_y is None else palm_y, finger_count, now, index_middle)
        self._update_swipe_gesture(x, finger_count, now)
        return point

    def active_gesture(self, now: float | None = None) -> str | None:
        timestamp = time.monotonic() if now is None else now
        if self._dragging:
            return "DRAGGING"
        if timestamp - self._last_action_time <= 0.8:
            return self.last_gesture
        return None

    def _update_pose_gestures(self, y: float, finger_count: int, now: float, index_middle: bool = False) -> None:
        if not self.mouse.enabled and not self.gesture_preview:
            self._last_finger_count = finger_count
            self._last_scroll_y = y if index_middle else None
            return
        if finger_count == 0:
            if self._last_finger_count != 0 and now - self._last_click >= 0.6:
                if self.mouse.enabled:
                    pyautogui.click(button="left")
                self._last_click = now
                self._set_gesture("fist click", now)
            self._last_scroll_y = None
        elif index_middle:
            if self._last_scroll_y is not None:
                delta = self._last_scroll_y - y
                if abs(delta) >= 0.012:
                    scroll_direction = "up" if delta > 0 else "down"
                    if self.mouse.enabled:
                        pyautogui.scroll(max(-8, min(8, round(delta * 60))))
                    self._set_gesture(f"SCROLL {scroll_direction.upper()}", now)
                    self._last_scroll_y = y
            else:
                self._last_scroll_y = y
        else:
            self._last_scroll_y = None
        self._last_finger_count = finger_count

    def cancel_drag(self) -> None:
        if self._dragging:
            self.mouse.release_left()
            self._dragging = False
            self._pinching = False
        self._release_alt_switch(time.monotonic(), force=True)

    def _release_alt_switch(self, now: float, force: bool = False) -> None:
        if self._alt_switch_until and (force or now >= self._alt_switch_until):
            if self.mouse.enabled:
                pyautogui.keyUp("alt")
            self._alt_switch_until = 0.0

    def _update_swipe_gesture(self, x: float, finger_count: int, now: float) -> None:
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
