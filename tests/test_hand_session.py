from eye_mouse.hand_session import HandSession


def test_hand_coordinates_map_to_screen():
    session = HandSession((1000, 800), smoothing=1.0, mouse_enabled=True)
    point = session.update(0.5, 0.25, False)
    assert point.x == 499.5
    assert point.y == 199.75


def test_hand_swipe_shortcut(monkeypatch):
    calls = []
    monkeypatch.setattr("pyautogui.hotkey", lambda *keys: calls.append(keys))
    session = HandSession((1000, 800), smoothing=1.0, mouse_enabled=True)
    session.update(0.20, 0.5, False, 5, (True, True, True, True, True))
    session._gesture_start_time -= 0.2
    session.update(0.45, 0.5, False, 5, (True, True, True, True, True))
    assert calls == [("win", "ctrl", "left")]


def test_fist_clicks_once(monkeypatch):
    clicks = []
    monkeypatch.setattr("pyautogui.click", lambda **kwargs: clicks.append(kwargs))
    session = HandSession((1000, 800), smoothing=1.0, mouse_enabled=True)
    session.update(0.5, 0.5, False, 1)
    session.update(0.5, 0.5, False, 0)
    session.update(0.5, 0.5, False, 0)
    assert clicks == [{"button": "left"}]


def test_two_finger_scroll(monkeypatch):
    scrolls = []
    monkeypatch.setattr("pyautogui.scroll", lambda amount: scrolls.append(amount))
    session = HandSession((1000, 800), smoothing=1.0, mouse_enabled=True)
    index_middle = (False, True, True, False, False)
    session.update(0.5, 0.6, False, 2, index_middle)
    session.update(0.5, 0.5, False, 2, index_middle)
    assert scrolls == [6]


def test_pinch_click_does_not_move_cursor(monkeypatch):
    clicks = []
    moves = []
    monkeypatch.setattr("pyautogui.click", lambda **kwargs: clicks.append(kwargs))
    monkeypatch.setattr("pyautogui.moveTo", lambda *args, **kwargs: moves.append(args))
    session = HandSession((1000, 800), smoothing=1.0, mouse_enabled=True)
    session.update(0.2, 0.5, False, 1)
    session.update(0.25, 0.5, True, 1)
    assert clicks == [{"button": "left"}]
    assert len(moves) == 1
