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
        axis = (0.08, 0.36, 0.64, 0.92)
        self.points = [
            (x, y) for y in axis for x in axis
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
            canvas.create_text(self.screen_width // 2, 76, text="Look at the dot with your eyes; keep your head still", fill="#aab6c5", font=("Segoe UI", 13))
            canvas.create_oval(x - 16, y - 16, x + 16, y + 16, fill="#ff4d6d", outline="white", width=3)
            window.update()
            start = time.monotonic()
            samples: list[np.ndarray] = []
            while time.monotonic() - start < 1.60:
                frame = camera.read()
                if frame is None:
                    continue
                result = self.tracker.process(frame)
                if result.face_detected and time.monotonic() - start > 0.60:
                    samples.append(result.features.vector)
                window.update()
                window.after(1)
            if samples:
                sample_array = np.asarray(samples)
                center = np.median(sample_array, axis=0)
                distances = np.linalg.norm(sample_array - center, axis=1)
                keep = distances <= np.percentile(distances, 75)
                features.append(np.mean(sample_array[keep], axis=0))
                targets.append(GazePoint(x, y))
        window.destroy()
        if len(features) < 3:
            raise RuntimeError("Calibration failed: face landmarks were not detected reliably")
        estimator = GazeEstimator((self.screen_width, self.screen_height))
        error = estimator.fit(features, targets)
        return estimator, error
