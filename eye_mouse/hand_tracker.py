from __future__ import annotations

import time
import urllib.request
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np


class HandTracker:
    def __init__(self) -> None:
        model_path = Path(__file__).with_name("hand_landmarker.task")
        if not model_path.exists():
            urllib.request.urlretrieve(
                "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
                model_path,
            )
        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(model_path)),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.55,
            min_hand_presence_confidence=0.55,
            min_tracking_confidence=0.55,
        )
        self._landmarker = mp.tasks.vision.HandLandmarker.create_from_options(options)
        self._timestamp_ms = 0

    def process(self, frame: np.ndarray) -> tuple[float, float, bool, int] | None:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        self._timestamp_ms = max(self._timestamp_ms + 1, round(time.monotonic() * 1000))
        result = self._landmarker.detect_for_video(image, self._timestamp_ms)
        if not result.hand_landmarks:
            return None
        landmarks = result.hand_landmarks[0]
        index_tip = landmarks[8]
        thumb_tip = landmarks[4]
        pinch_distance = np.hypot(index_tip.x - thumb_tip.x, index_tip.y - thumb_tip.y)
        finger_count = self._count_extended_fingers(landmarks)
        return float(index_tip.x), float(index_tip.y), bool(pinch_distance < 0.055), finger_count

    @staticmethod
    def _count_extended_fingers(landmarks) -> int:
        wrist = landmarks[0]
        count = 0
        for tip_index, joint_index in ((8, 6), (12, 10), (16, 14), (20, 18)):
            tip = landmarks[tip_index]
            joint = landmarks[joint_index]
            if np.hypot(tip.x - wrist.x, tip.y - wrist.y) > np.hypot(joint.x - wrist.x, joint.y - wrist.y):
                count += 1
        return count

    def close(self) -> None:
        self._landmarker.close()
