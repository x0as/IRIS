# Project IRIS

Project IRIS is a webcam-based eye-controlled mouse for Windows. It uses OpenCV and MediaPipe Face Mesh to estimate gaze after a per-session nine-point calibration, then optionally moves the primary-monitor cursor. A separate always-on-top gaze dot makes the estimate visible.

This is approximate webcam gaze estimation, not medical-grade eye tracking. Dedicated infrared hardware will be more accurate.

## Install

Use Python 3.10 or newer, then from this directory run:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Controls

- Hand mode pinch: left click
- Index finger only: move the cursor
- Index + middle fingers: move vertically to scroll down
- Middle + ring fingers: move vertically to scroll up
- Thumb + index pinch: left click
- In Hand Control Mode, move your open palm left to go to the right desktop, or right to go to the left desktop.
- In Hand Control Mode, a 3-finger horizontal swipe sends `Alt+Shift+Tab` or `Alt+Tab` to switch apps.
- `HAND TEST MODE` shows recognized hand gestures and pointer feedback without sending mouse clicks, scrolling, or Windows shortcuts.
- `DOUBLE MODE` requires no gaze calibration. It uses hand control for the cursor: hold the left eye closed to switch virtual desktops left (`Win+Ctrl+Left`), hold the right eye closed to switch virtual desktops right (`Win+Ctrl+Right`), double-blink the left eye for left click, and double-blink the right eye for right click.
- Hand commands require the thumb to be visibly extended outward; a folded-thumb pose is ignored except for fist detection.

The default session starts with mouse control disabled. The primary monitor resolution is detected dynamically. If the face is lost, the last cursor position is frozen and gesture processing stops until landmarks return.

## Camera and lighting

Use a built-in webcam at roughly eye level. Sit about 40-80 cm from the display, keep the face visible, and avoid strong backlighting. The app requests a moderate camera resolution and is designed for ordinary laptop CPUs.

Low-light enhancement is enabled by default. The camera uses auto-exposure plus adaptive contrast and brightness enhancement before landmark detection. It helps in dim rooms, but the webcam still needs some visible light on your face; complete darkness cannot be recovered by software.

## Tests

Run deterministic tests for the calibration mapper, smoothing, and blink state machine with:

```powershell
python -m pytest
```

Hardware-dependent webcam, MediaPipe, overlay, and OS mouse behavior must be tested on the target machine with a real camera. Check Windows privacy permissions if the camera cannot open.

## Limitations

The initial version targets one primary monitor and does not compensate for glasses, extreme head pose, poor lighting, or large camera movement. Calibration data is not reused silently between sessions; this avoids applying a model to a changed camera or screen setup. The architecture leaves room for dwell-click and multi-monitor support.
