from eye_mouse.hand_session import HandSession


def test_hand_coordinates_map_to_screen():
    session = HandSession((1000, 800), smoothing=1.0, mouse_enabled=True)
    point = session.update(0.5, 0.25, False)
    assert point.x == 499.5
    assert point.y == 199.75


def test_hand_swipe_shortcut(monkeypatch):
    calls = []
    monkeypatch.setattr("pyautogui.hotkey", lambda *keys: calls.append(keys))
    session = HandSession((1000, 800), smoothing=1.0, mouse_enabled=False)
    session.update(0.20, 0.5, False, 4)
    session._gesture_start_time -= 0.2
    session.update(0.45, 0.5, False, 4)
    assert calls == [("win", "ctrl", "right")]
