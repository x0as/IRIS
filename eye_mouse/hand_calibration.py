from __future__ import annotations

import time
import tkinter as tk

import numpy as np

from .gaze_estimator import GazeEstimator
from .hand_tracker import HandTracker
from .models import GazePoint


class HandCalibration:
    def __init__(self, root: tk.Tk, tracker: HandTracker, screen_size: tuple[int, int]) -> None:
        self.root = root
        self.tracker = tracker
        self.width, self.height = screen_size
        axis = (0.10, 0.30, 0.50, 0.70, 0.90)
        self.points = [(x, y) for y in axis for x in axis]

    def run(self, camera) -> tuple[GazeEstimator, float]:
        window = tk.Toplevel(self.root)
        window.attributes("-fullscreen", True)
        window.attributes("-topmost", True)
        canvas = tk.Canvas(window, bg="#10151c", highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        features: list[np.ndarray] = []
        targets: list[GazePoint] = []
        for index, (x_ratio, y_ratio) in enumerate(self.points):
            x, y = round(self.width * x_ratio), round(self.height * y_ratio)
            canvas.delete("all")
            canvas.create_text(self.width // 2, 42, text=f"Hand calibration {index + 1} / {len(self.points)}", fill="white", font=("Segoe UI", 18))
            canvas.create_text(self.width // 2, 76, text="Place your index fingertip on the dot and hold it still", fill="#aab6c5", font=("Segoe UI", 13))
            canvas.create_oval(x - 16, y - 16, x + 16, y + 16, fill="#ff4d6d", outline="white", width=3)
            window.update()
            started = time.monotonic()
            samples: list[np.ndarray] = []
            while time.monotonic() - started < 1.1:
                frame = camera.read()
                if frame is not None:
                    observation = self.tracker.process(frame)
                    if observation is not None and time.monotonic() - started > 0.35:
                        samples.append(np.array(observation[:2]))
                window.update()
                window.after(1)
            if samples:
                features.append(np.median(np.asarray(samples), axis=0))
                targets.append(GazePoint(x, y))
        window.destroy()
        if len(features) < 6:
            raise RuntimeError("Hand calibration failed: keep your hand visible and try again")
        estimator = GazeEstimator((self.width, self.height))
        return estimator, estimator.fit(features, targets)