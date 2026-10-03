from eye_mouse.wink_detector import RightEyeDoubleBlink


def test_right_eye_double_blink():
    detector = RightEyeDoubleBlink()
    assert detector.update(0.1, 1.0) is False
    assert detector.update(0.3, 1.12) is False
    assert detector.update(0.1, 1.30) is False
    assert detector.update(0.3, 1.42) is True


def test_long_right_eye_closure_is_ignored():
    detector = RightEyeDoubleBlink()
    detector.update(0.1, 1.0)
    assert detector.update(0.3, 1.6) is False