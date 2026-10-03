from __future__ import annotations

import time

from .blink_detector import BlinkAction, BlinkDetector
from .config import Settings
from .gaze_estimator import GazeEstimator
from .models import GazePoint
from .mouse_controller import MouseController
from .smoothing import ExponentialSmoother
from .wink_detector import RightEyeDoubleBlink


class TrackingSession:
    def __init__(self, settings: Settings, estimator: GazeEstimator, double_mode: bool = False) -> None:
        self.settings = settings
        self.estimator = estimator
        self.smoother = ExponentialSmoother(settings.smoothing)
        self.blink_detector = BlinkDetector(settings.blink_ear_threshold, settings.min_blink_duration, settings.long_blink_duration, settings.max_blink_duration, settings.double_blink_window, settings.click_cooldown)
        self.double_mode = double_mode
        self.wink_detector = RightEyeDoubleBlink(settings.blink_ear_threshold, cooldown=settings.click_cooldown)
        self.mouse = MouseController(settings.mouse_control_enabled)
        self.last_raw: GazePoint | None = None
        self.last_smoothed: GazePoint | None = None
        self.last_action = "None"
        self.paused = False

    def update(self, features, timestamp: float | None = None) -> GazePoint | None:
        if self.paused or features is None:
            return self.last_smoothed
        timestamp = time.monotonic() if timestamp is None else timestamp
        self.last_raw = self.estimator.predict(features.vector)
        self.last_smoothed = self.smoother.update(self.last_raw)
        self.mouse.move_to(self.last_smoothed)
        action = self.blink_detector.update(features.ear, timestamp)
        self.blink_detector.expire_pending(timestamp)
        if self.double_mode:
            action = BlinkAction.RIGHT_CLICK if self.wink_detector.update(features.right_ear, timestamp) else None
            self.wink_detector.expire(timestamp)
        if action is not None:
            self.mouse.click(action)
            self.last_action = action.value
        return self.last_smoothed
