from eye_mouse.hand_session import HandSession


def test_hand_coordinates_map_to_screen():
    session = HandSession((1000, 800), smoothing=1.0, mouse_enabled=False)
    point = session.update(0.5, 0.25, False)
    assert point.x == 499.5
    assert point.y == 199.75
