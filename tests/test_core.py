import numpy as np
import pytest

from eye_mouse.blink_detector import BlinkAction, BlinkDetector
from eye_mouse.gaze_estimator import GazeEstimator
from eye_mouse.models import GazePoint
from eye_mouse.smoothing import ExponentialSmoother


def test_smoother_reduces_jump():
    smoother = ExponentialSmoother(0.2)
    smoother.update(GazePoint(0, 0))
    point = smoother.update(GazePoint(100, 100))
    assert point.x == 20
    assert point.y == 20


def test_calibration_model_maps_training_points():
    estimator = GazeEstimator((1000, 800))
    features = [np.array([x, y]) for x, y in ((0, 0), (1, 0), (0, 1), (1, 1), (0.5, 0.5))]
    targets = [GazePoint(x * 900 + 50, y * 700 + 50) for x, y in ((0, 0), (1, 0), (0, 1), (1, 1), (0.5, 0.5))]
    error = estimator.fit(features, targets)
    assert error < 1e-6
    assert estimator.predict(np.array([0, 0])).x == pytest.approx(50)


def test_two_short_blinks_left_click():
    detector = BlinkDetector(0.2, 0.05, 0.5, 1.5, 0.7, 0.0)
    assert detector.update(0.1, 1.0) is None
    assert detector.update(0.3, 1.2) is None
    assert detector.update(0.1, 1.4) is None
    assert detector.update(0.3, 1.6) == BlinkAction.LEFT_CLICK


def test_long_blink_right_click():
    detector = BlinkDetector(0.2, 0.05, 0.5, 1.5, 0.7, 0.0)
    detector.update(0.1, 1.0)
    assert detector.update(0.3, 1.7) == BlinkAction.RIGHT_CLICK
