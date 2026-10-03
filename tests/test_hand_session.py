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


def test_three_finger_swipe_opens_app_switcher(monkeypatch):
    events = []
    monkeypatch.setattr("pyautogui.keyDown", lambda key: events.append(("down", key)))
    monkeypatch.setattr("pyautogui.keyUp", lambda key: events.append(("up", key)))
    monkeypatch.setattr("pyautogui.press", lambda key: events.append(("press", key)))
    session = HandSession((1000, 800), smoothing=1.0, mouse_enabled=True)
    fingers = (False, True, True, True, False)
    session.update(0.20, 0.5, False, 3, fingers)
    session._gesture_start_time -= 0.2
    session.update(0.45, 0.5, False, 3, fingers)
    assert events[:2] == [("down", "alt"), ("press", "tab")]
    session._release_alt_switch(0.0, force=True)
    assert events[-1] == ("up", "alt")


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
    session.update(0.5, 0.6, False, 2, index_middle, 0.6)
    session.update(0.5, 0.5, False, 2, index_middle, 0.5)
    assert scrolls == [-6]
    assert session.last_gesture == "SCROLL DOWN"


def test_middle_ring_scrolls_up(monkeypatch):
    scrolls = []
    monkeypatch.setattr("pyautogui.scroll", lambda amount: scrolls.append(amount))
    session = HandSession((1000, 800), smoothing=1.0, mouse_enabled=True)
    middle_ring = (False, False, True, True, False)
    session.update(0.5, 0.6, False, 2, middle_ring, 0.6)
    session.update(0.5, 0.5, False, 2, middle_ring, 0.5)
    assert scrolls == [6]
    assert session.last_gesture == "SCROLL UP"


def test_two_finger_neutral_does_not_scroll(monkeypatch):
    scrolls = []
    monkeypatch.setattr("pyautogui.scroll", lambda amount: scrolls.append(amount))
    session = HandSession((1000, 800), smoothing=1.0, mouse_enabled=True)
    index_middle = (False, True, True, False, False)
    session.update(0.5, 0.5, False, 2, index_middle, 0.5)
    session.update(0.5, 0.5, False, 2, index_middle, 0.505)
    assert scrolls == []


def test_pinch_click_does_not_move_cursor(monkeypatch):
    clicks = []
    presses = []
    releases = []
    moves = []
    monkeypatch.setattr("pyautogui.click", lambda **kwargs: clicks.append(kwargs))
    monkeypatch.setattr("pyautogui.mouseDown", lambda **kwargs: presses.append(kwargs))
    monkeypatch.setattr("pyautogui.mouseUp", lambda **kwargs: releases.append(kwargs))
    monkeypatch.setattr("pyautogui.moveTo", lambda *args, **kwargs: moves.append(args))
    session = HandSession((1000, 800), smoothing=1.0, mouse_enabled=True)
    session.update(0.2, 0.5, False, 1)
    session.update(0.25, 0.5, True, 1)
    session._pinch_started_at -= 0.6
    session.update(0.35, 0.5, True, 1, index_near=True)
    session.update(0.35, 0.5, False, 1)
    assert clicks == []
    assert presses == [{"button": "left"}]
    assert releases == [{"button": "left"}]
    assert len(moves) == 2
    assert moves[-1] != moves[0]


def test_middle_thumb_has_no_click_action(monkeypatch):
    clicks = []
    moves = []
    monkeypatch.setattr("pyautogui.click", lambda **kwargs: clicks.append(kwargs))
    monkeypatch.setattr("pyautogui.moveTo", lambda *args, **kwargs: moves.append(args))
    session = HandSession((1000, 800), smoothing=1.0, mouse_enabled=True)
    session.update(0.2, 0.5, False, 1, (False, True, False, False, False))
    session.update(0.5, 0.5, False, 2, (True, True, True, False, False), middle_pinching=True, middle_near=True)
    session.update(0.7, 0.5, False, 2, (True, True, True, False, False), middle_pinching=True, middle_near=True)
    assert clicks == []
    assert len(moves) == 1
