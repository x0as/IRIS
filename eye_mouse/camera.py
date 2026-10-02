from __future__ import annotations

import cv2


class Camera:
    def __init__(self, index: int, width: int, height: int, low_light: bool = True) -> None:
        self.index = index
        self.width = width
        self.height = height
        self.low_light = low_light
        self.capture: cv2.VideoCapture | None = None

    def open(self) -> None:
        self.capture = cv2.VideoCapture(self.index)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.capture.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)
        if not self.capture.isOpened():
            raise RuntimeError(f"Could not open webcam {self.index}")

    def read(self):
        if self.capture is None:
            raise RuntimeError("Camera is not open")
        ok, frame = self.capture.read()
        if not ok or frame is None:
            return None
        frame = cv2.flip(frame, 1)
        return self._enhance_low_light(frame) if self.low_light else frame

    @staticmethod
    def _enhance_low_light(frame):
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        lightness, a_channel, b_channel = cv2.split(lab)
        average_lightness = float(lightness.mean())
        if average_lightness < 115:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            lightness = clahe.apply(lightness)
            gain = min(1.65, 115.0 / max(average_lightness, 1.0))
            lightness = cv2.convertScaleAbs(lightness, alpha=gain, beta=0)
        return cv2.cvtColor(cv2.merge((lightness, a_channel, b_channel)), cv2.COLOR_LAB2BGR)

    def close(self) -> None:
        if self.capture is not None:
            self.capture.release()
            self.capture = None
