from dataclasses import dataclass


@dataclass
class Settings:
    camera_index: int = 0
    camera_width: int = 960
    camera_height: int = 540
    smoothing: float = 0.22
    blink_ear_threshold: float = 0.20
    min_blink_duration: float = 0.08
    long_blink_duration: float = 0.55
    max_blink_duration: float = 1.8
    double_blink_window: float = 0.65
    click_cooldown: float = 0.8
    indicator_enabled: bool = True
    indicator_size: int = 18
    indicator_opacity: float = 0.9
    mouse_control_enabled: bool = False
    debug: bool = False
