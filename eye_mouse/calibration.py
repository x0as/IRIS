from __future__ import annotations

import time
import tkinter as tk

import numpy as np

from .face_tracker import FaceTracker
from .gaze_estimator import GazeEstimator
from .models import GazePoint


class Calibration:
    def __init__(self, root: tk.Tk, tracker: FaceTracker, screen_size: tuple[int, int]) -> None:
        self.root = root
        self.tracker = tracker
        self.screen_width, self.screen_height = screen_size
        self.points = [
            (0.08, 0.10), (0.50, 0.10), (0.92, 0.10),
            (0.08, 0.50), (0.50, 0.50), (0.92, 0.50),
            (0.08, 0.90), (0.50, 0.90), (0.92, 0.90),
        ]

    def run(self, camera) -> tuple[GazeEstimator, float]:
        window = tk.Toplevel(self.root)
        window.attributes("-fullscreen", True)
        window.attributes("-topmost", True)
        window.configure(bg="#10151c")
        canvas = tk.Canvas(window, bg="#10151c", highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        features: list[np.ndarray] = []
        targets: list[GazePoint] = []
        window.update()
        for index, (x_ratio, y_ratio) in enumerate(self.points):
            x, y = round(self.screen_width * x_ratio), round(self.screen_height * y_ratio)
            canvas.delete("all")
            canvas.create_text(self.screen_width // 2, 42, text=f"Calibration {index + 1} / {len(self.points)}", fill="white", font=("Segoe UI", 18))
            canvas.create_text(self.screen_width // 2, 76, text="Look at the dot and hold your gaze", fill="#aab6c5", font=("Segoe UI", 13))
            canvas.create_oval(x - 16, y - 16, x + 16, y + 16, fill="#ff4d6d", outline="white", width=3)
            window.update()
            start = time.monotonic()
            samples: list[np.ndarray] = []
            while time.monotonic() - start < 1.25:
                frame = camera.read()
                if frame is None:
                    continue
                result = self.tracker.process(frame)
                if result.face_detected and time.monotonic() - start > 0.35:
                    samples.append(result.features.vector)
                window.update()
                window.after(1)
            if samples:
                features.append(np.mean(samples, axis=0))
                targets.append(GazePoint(x, y))
        window.destroy()
        if len(features) < 3:
            raise RuntimeError("Calibration failed: face landmarks were not detected reliably")
        estimator = GazeEstimator((self.screen_width, self.screen_height))
        error = estimator.fit(features, targets)
        return estimator, error
