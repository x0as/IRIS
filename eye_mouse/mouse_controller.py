from __future__ import annotations

import pyautogui

from .blink_detector import BlinkAction
from .models import GazePoint


class MouseController:
    def __init__(self, enabled: bool = False) -> None:
        self.enabled = enabled
        pyautogui.PAUSE = 0
        pyautogui.FAILSAFE = True

    def move_to(self, point: GazePoint) -> None:
        if self.enabled:
            pyautogui.moveTo(round(point.x), round(point.y), duration=0)

    def click(self, action: BlinkAction) -> None:
        if not self.enabled:
            return
        pyautogui.click(button="left" if action == BlinkAction.LEFT_CLICK else "right")

