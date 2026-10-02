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

## Run

```powershell
python main.py
```

Choose `START CALIBRATION`, look at each dot until it advances, then use `PREVIEW MODE` first. Preview mode moves the visible gaze indicator but never moves or clicks the OS mouse. `MOUSE CONTROL MODE` enables cursor movement and blink clicks.

If gaze tracking is not reliable enough for your camera or lighting, use `HAND CONTROL MODE`. The detected index fingertip is mapped directly from the camera view to the primary screen and smoothed for cursor control.

## Controls

- `ESC`: stop tracking and disable mouse actions
- `F8`: pause or resume tracking
- `C`: stop and recalibrate
- Two short blinks: left click
- One longer blink: right click
- Hand mode pinch: left click
- Fist transition: single left click
- Two fingers with vertical movement: scroll up or down
- In Hand Control Mode, an open-palm horizontal swipe sends `Win+Ctrl+Left/Right` to change virtual desktops.
- In Hand Control Mode, a 3-finger horizontal swipe sends `Alt+Shift+Tab` or `Alt+Tab` to switch apps.
- `HAND TEST MODE` shows recognized hand gestures and pointer feedback without sending mouse clicks, scrolling, or Windows shortcuts.

The default session starts with mouse control disabled. The primary monitor resolution is detected dynamically. If the face is lost, the last cursor position is frozen and gesture processing stops until landmarks return.

## Camera and lighting

Use a built-in webcam at roughly eye level. Sit about 40-80 cm from the display, keep the face visible, and avoid strong backlighting. The app requests a moderate camera resolution and is designed for ordinary laptop CPUs.

## Tests

Run deterministic tests for the calibration mapper, smoothing, and blink state machine with:

```powershell
python -m pytest
```

Hardware-dependent webcam, MediaPipe, overlay, and OS mouse behavior must be tested on the target machine with a real camera. Check Windows privacy permissions if the camera cannot open.

## Limitations

The initial version targets one primary monitor and does not compensate for glasses, extreme head pose, poor lighting, or large camera movement. Calibration data is not reused silently between sessions; this avoids applying a model to a changed camera or screen setup. The architecture leaves room for dwell-click and multi-monitor support.
