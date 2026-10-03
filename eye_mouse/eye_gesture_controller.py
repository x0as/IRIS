from __future__ import annotations

import time
from dataclasses import dataclass

import pyautogui


@dataclass
class EyeGestureController:
    threshold: float = 0.20
    minimum_blink: float = 0.06
    maximum_blink: float = 0.45
    double_window: float = 0.70
    hold_duration: float = 0.70
    cooldown: float = 0.80

    def __post_init__(self) -> None:
        self._closed_since = {"left": None, "right": None}
        self._last_blink = {"left": None, "right": None}
        self._hold_sent = {"left": False, "right": False}
        self._cooldown_until = 0.0
        self.last_action = "None"

    def update(self, left_ear: float, right_ear: float, timestamp: float | None = None) -> str | None:
        now = time.monotonic() if timestamp is None else timestamp
        actions: list[str] = []
        for eye, ear in (("left", left_ear), ("right", right_ear)):
            closed = ear < self.threshold
            started = self._closed_since[eye]
            if closed:
                if started is None:
                    self._closed_since[eye] = now
                elif not self._hold_sent[eye] and now - started >= self.hold_duration and now >= self._cooldown_until:
                    direction = "left" if eye == "left" else "right"
                    if pyautogui is not None:
                        if direction == "left":
                            pyautogui.hotkey("alt", "shift", "tab")
                        else:
                            pyautogui.hotkey("alt", "tab")
                    self._hold_sent[eye] = True
                    self._cooldown_until = now + self.cooldown
                    actions.append(f"SWITCH WINDOW {direction.upper()}")
                continue
            if started is None:
                continue
            duration = now - started
            self._closed_since[eye] = None
            self._hold_sent[eye] = False
            if duration < self.minimum_blink or duration > self.maximum_blink or now < self._cooldown_until:
                continue
            previous = self._last_blink[eye]
            if previous is not None and now - previous <= self.double_window:
                action = "LEFT CLICK" if eye == "left" else "RIGHT CLICK"
                if pyautogui is not None:
                    pyautogui.click(button="left" if eye == "left" else "right")
                self._last_blink[eye] = None
                self._cooldown_until = now + self.cooldown
                actions.append(action)
            else:
                self._last_blink[eye] = now
        for eye in ("left", "right"):
            if self._last_blink[eye] is not None and now - self._last_blink[eye] > self.double_window:
                self._last_blink[eye] = None
        self.last_action = actions[-1] if actions else self.last_action
        return actions[-1] if actions else None