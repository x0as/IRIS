from __future__ import annotations

import math
import time
import urllib.request
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np

from .models import EyeFeatures, TrackingResult


class FaceTracker:
    def __init__(self, debug: bool = False) -> None:
        self.debug = debug
        model_path = Path(__file__).with_name("face_landmarker.task")
        if not model_path.exists():
            urllib.request.urlretrieve(
                "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
                model_path,
            )
        options = mp.tasks.vision.FaceLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(model_path)),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_faces=1,
            min_face_detection_confidence=0.55,
            min_face_presence_confidence=0.55,
            min_tracking_confidence=0.55,
        )
        self._mesh = mp.tasks.vision.FaceLandmarker.create_from_options(options)
        self._timestamp_ms = 0

    @staticmethod
    def _distance(a: np.ndarray, b: np.ndarray) -> float:
        return float(np.linalg.norm(a - b))

    def process(self, frame: np.ndarray) -> TrackingResult:
        height, width = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        self._timestamp_ms = max(self._timestamp_ms + 1, round(time.monotonic() * 1000))
        result = self._mesh.detect_for_video(image, self._timestamp_ms)
        if not result.face_landmarks:
            return TrackingResult(frame=frame, face_detected=False)

        landmarks = result.face_landmarks[0]
        points = np.array([(landmark.x * width, landmark.y * height) for landmark in landmarks])
        left_corners = (points[33], points[133])
        right_corners = (points[362], points[263])
        left_iris = points[468:473].mean(axis=0)
        right_iris = points[473:478].mean(axis=0)

        left_width = max(self._distance(*left_corners), 1.0)
        right_width = max(self._distance(*right_corners), 1.0)
        left_ratio = (left_iris - left_corners[0]) / left_width
        right_ratio = (right_iris - right_corners[0]) / right_width
        face_center = points[1] / np.array([width, height])
        face_width = max(self._distance(points[234], points[454]), 1.0)
        face_scale = face_width / width
        ear_values = [
            self._eye_aspect_ratio(points, (33, 160, 158, 133, 153, 144)),
            self._eye_aspect_ratio(points, (362, 385, 387, 263, 373, 380)),
        ]
        ear = float(sum(ear_values) / len(ear_values))
        vector = np.array(
            [left_ratio[0], left_ratio[1], right_ratio[0], right_ratio[1], face_center[0], face_center[1], face_scale],
            dtype=float,
        )
        if self.debug:
            debug_frame = frame.copy()
            for point in points[[33, 133, 362, 263, 468, 473]]:
                cv2.circle(debug_frame, tuple(point.astype(int)), 3, (0, 255, 0), -1)
            frame = debug_frame
        return TrackingResult(
            features=EyeFeatures(vector, ear, tuple(left_iris), tuple(right_iris)),
            face_detected=True,
            frame=frame,
        )

    @staticmethod
    def _eye_aspect_ratio(points: np.ndarray, indices: tuple[int, int, int, int, int, int]) -> float:
        left, upper_left, upper_right, right, lower_right, lower_left = (points[index] for index in indices)
        horizontal = FaceTracker._distance(left, right)
        return (FaceTracker._distance(upper_left, lower_left) + FaceTracker._distance(upper_right, lower_right)) / max(2 * horizontal, 1.0)

    def close(self) -> None:
        self._mesh.close()
