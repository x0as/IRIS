from eye_mouse.eye_gesture_controller import EyeGestureController


def test_double_eye_blinks_click_by_side(monkeypatch):
    clicks = []
    monkeypatch.setattr("pyautogui.click", lambda **kwargs: clicks.append(kwargs))
    controller = EyeGestureController()
    controller.update(0.1, 0.3, 1.0)
    controller.update(0.3, 0.3, 1.12)
    controller.update(0.1, 0.3, 1.30)
    controller.update(0.3, 0.3, 1.42)
    assert clicks == [{"button": "left"}]


def test_held_eye_switches_window(monkeypatch):
    shortcuts = []
    monkeypatch.setattr("pyautogui.hotkey", lambda *keys: shortcuts.append(keys))
    controller = EyeGestureController()
    controller.update(0.1, 0.3, 1.0)
    controller.update(0.1, 0.3, 1.8)
    assert shortcuts == [("win", "ctrl", "left")]