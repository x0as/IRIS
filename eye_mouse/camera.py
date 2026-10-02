from __future__ import annotations

import cv2


class Camera:
    def __init__(self, index: int, width: int, height: int) -> None:
        self.index = index
        self.width = width
        self.height = height
        self.capture: cv2.VideoCapture | None = None

    def open(self) -> None:
        self.capture = cv2.VideoCapture(self.index)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        if not self.capture.isOpened():
            raise RuntimeError(f"Could not open webcam {self.index}")

    def read(self):
        if self.capture is None:
            raise RuntimeError("Camera is not open")
        ok, frame = self.capture.read()
        if not ok or frame is None:
            return None
        return cv2.flip(frame, 1)

    def close(self) -> None:
        if self.capture is not None:
            self.capture.release()
            self.capture = None
