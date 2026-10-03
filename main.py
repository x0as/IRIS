from __future__ import annotations

import time
import tkinter as tk
from tkinter import messagebox

import cv2

from eye_mouse.calibration import Calibration
from eye_mouse.camera import Camera
from eye_mouse.config import Settings
from eye_mouse.face_tracker import FaceTracker
from eye_mouse.gaze_overlay import GazeOverlay
from eye_mouse.eye_gesture_controller import EyeGestureController
from eye_mouse.hand_session import HandSession
from eye_mouse.hand_tracker import HandTracker
from eye_mouse.screen import primary_screen_size
from eye_mouse.tracking_session import TrackingSession


class EyeMouseApp:
    def __init__(self) -> None:
        self.settings = Settings()
        self.root = tk.Tk()
        self.root.title("Project IRIS")
        self.root.geometry("500x560")
        self.root.configure(bg="#10151c")
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.bind("<Escape>", lambda _event: self.stop_tracking())
        self.root.bind("<F8>", lambda _event: self.toggle_pause())
        self.root.bind("c", lambda _event: self.start_calibration())
        self.camera: Camera | None = None
        self.tracker: FaceTracker | None = None
        self.hand_tracker: HandTracker | None = None
        self.eye_gestures: EyeGestureController | None = None
        self.overlay: GazeOverlay | None = None
        self.session: TrackingSession | None = None
        self.estimator = None
        self.tracking = False
        self.paused = False
        self.tracking_mode = "gaze"
        self.screen_size = primary_screen_size()
        self.status = tk.StringVar(value="Preview mode. Calibrate before tracking.")
        self._build_ui()

    def _build_ui(self) -> None:
        container = tk.Frame(self.root, bg="#10151c")
        container.pack(fill="both", expand=True)
        canvas = tk.Canvas(container, bg="#10151c", highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        content = tk.Frame(canvas, bg="#10151c")
        content.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=content, anchor="nw", width=465)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(-int(event.delta / 120), "units"))
        tk.Label(content, text="PROJECT IRIS", fg="#ff4d6d", bg="#10151c", font=("Segoe UI", 26, "bold")).pack(pady=(28, 4))
        tk.Label(content, text="Webcam gaze and hand control", fg="#d8e0ea", bg="#10151c", font=("Segoe UI", 12)).pack(pady=(0, 20))
        for text, command in (("START CALIBRATION", self.start_calibration), ("GAZE PREVIEW", lambda: self.start_tracking(False)), ("GAZE MOUSE CONTROL", lambda: self.start_tracking(True)), ("DOUBLE MODE", lambda: self.start_tracking(True, True)), ("HAND TEST MODE", lambda: self.start_hand_tracking(False, True)), ("HAND CONTROL MODE", lambda: self.start_hand_tracking(True, False)), ("SETTINGS", self.show_settings), ("STOP / ESC", self.stop_tracking), ("EXIT", self.close)):
            tk.Button(content, text=text, command=command, width=28, height=2, bg="#1c2633", fg="white", activebackground="#2c3a4d", activeforeground="white", relief="flat", font=("Segoe UI", 10, "bold")).pack(pady=5)
        tk.Label(content, textvariable=self.status, fg="#aab6c5", bg="#10151c", wraplength=390, font=("Segoe UI", 10)).pack(pady=18)
        tk.Label(content, text="ESC stops  |  F8 pauses/resumes  |  C recalibrates  |  Scroll for all controls", fg="#738196", bg="#10151c", font=("Segoe UI", 9)).pack(pady=16)

    def _ensure_hardware(self) -> None:
        if self.camera is None:
            self.camera = Camera(self.settings.camera_index, self.settings.camera_width, self.settings.camera_height, self.settings.low_light_enhancement)
            self.camera.open()
        if self.tracker is None:
            self.tracker = FaceTracker(self.settings.debug)

    def _ensure_hand_hardware(self) -> None:
        if self.camera is None:
            self.camera = Camera(self.settings.camera_index, self.settings.camera_width, self.settings.camera_height, self.settings.low_light_enhancement)
            self.camera.open()
        if self.hand_tracker is None:
            self.hand_tracker = HandTracker()

    def start_calibration(self) -> None:
        try:
            self.stop_tracking()
            self.status.set("Opening camera for calibration...")
            self.root.update()
            self._ensure_hardware()
            self.status.set("Calibration running. Follow the target dots...")
            self.root.update()
            self.estimator, error = Calibration(self.root, self.tracker, self.screen_size).run(self.camera)
            self.status.set(f"Calibration complete. Average error: {error:.0f}px")
            if error > 180:
                messagebox.showwarning("Low calibration accuracy", "Accuracy is low. Try better lighting and keep your face visible.")
        except Exception as exc:
            messagebox.showerror("Calibration error", str(exc))
            self.status.set("Calibration failed. Check the webcam and try again.")

    def start_tracking(self, mouse_enabled: bool, double_mode: bool = False) -> None:
        if not double_mode and self.estimator is None:
            self.start_calibration()
            if self.estimator is None:
                return
        try:
            if double_mode:
                self.stop_tracking()
                self.status.set("Opening camera for hand and eye-gesture control...")
                self.root.update()
                self._ensure_hand_hardware()
                self._ensure_hardware()
                self.hand_session = HandSession(self.screen_size, self.settings.smoothing, mouse_enabled)
                self.eye_gestures = EyeGestureController(self.settings.blink_ear_threshold, cooldown=self.settings.click_cooldown)
                self.tracking_mode = "double"
                self.tracking = True
                self.paused = False
                self.overlay = GazeOverlay(self.settings.indicator_size, self.settings.indicator_opacity) if self.settings.indicator_enabled else None
                self.status.set("Double mode: hand control + eye gestures, no gaze cursor.")
                self._tracking_tick()
                return
            self.status.set("Opening camera for gaze tracking...")
            self.root.update()
            self._ensure_hardware()
            self.settings.mouse_control_enabled = mouse_enabled
            self.session = TrackingSession(self.settings, self.estimator, double_mode)
            self.tracking_mode = "gaze"
            self.session.mouse.enabled = mouse_enabled
            self.overlay = GazeOverlay(self.settings.indicator_size, self.settings.indicator_opacity) if self.settings.indicator_enabled else None
            self.tracking = True
            self.paused = False
            mode = "double" if double_mode else ("mouse control" if mouse_enabled else "preview")
            self.status.set(f"Tracking in {mode} mode. ESC stops immediately.")
            self._tracking_tick()
        except Exception as exc:
            messagebox.showerror("Tracking error", str(exc))

    def start_hand_tracking(self, mouse_enabled: bool, gesture_preview: bool = False) -> None:
        try:
            self.stop_tracking()
            self.status.set("Opening camera and loading hand model...")
            self.root.update()
            self._ensure_hand_hardware()
            self.hand_session = HandSession(self.screen_size, self.settings.smoothing, mouse_enabled, gesture_preview)
            self.overlay = GazeOverlay(self.settings.indicator_size, self.settings.indicator_opacity) if self.settings.indicator_enabled else None
            self.tracking_mode = "hand"
            self.tracking = True
            self.paused = False
            self.status.set("Hand test mode active. Gestures are previewed safely." if gesture_preview else "Hand control active. Move your index finger; pinch thumb and index to click.")
            self._tracking_tick()
        except Exception as exc:
            messagebox.showerror("Hand tracking error", str(exc))

    def show_settings(self) -> None:
        window = tk.Toplevel(self.root)
        window.title("Project IRIS Settings")
        window.configure(bg="#10151c")
        window.resizable(False, False)
        fields = (("Cursor smoothing", "smoothing", 0.05, 1.0, 0.01), ("Blink threshold", "blink_ear_threshold", 0.10, 0.40, 0.01), ("Long blink seconds", "long_blink_duration", 0.30, 1.20, 0.05), ("Double-blink window", "double_blink_window", 0.30, 1.20, 0.05), ("Click cooldown", "click_cooldown", 0.20, 2.00, 0.05))
        for row, (label, name, minimum, maximum, step) in enumerate(fields):
            tk.Label(window, text=label, fg="white", bg="#10151c", anchor="w", width=22).grid(row=row, column=0, padx=12, pady=7)
            variable = tk.DoubleVar(value=getattr(self.settings, name))
            tk.Scale(window, variable=variable, from_=minimum, to=maximum, resolution=step, orient="horizontal", length=220, bg="#10151c", fg="white", highlightthickness=0, troughcolor="#2c3a4d", command=lambda value, setting=name, var=variable: setattr(self.settings, setting, var.get())).grid(row=row, column=1, padx=12, pady=7)
        indicator = tk.BooleanVar(value=self.settings.indicator_enabled)
        tk.Checkbutton(window, text="Show gaze indicator", variable=indicator, command=lambda: setattr(self.settings, "indicator_enabled", indicator.get()), fg="white", bg="#10151c", selectcolor="#2c3a4d", activebackground="#10151c", activeforeground="white").grid(row=len(fields), column=0, columnspan=2, pady=8)
        debug = tk.BooleanVar(value=self.settings.debug)
        tk.Checkbutton(window, text="Debug readout", variable=debug, command=lambda: setattr(self.settings, "debug", debug.get()), fg="white", bg="#10151c", selectcolor="#2c3a4d", activebackground="#10151c", activeforeground="white").grid(row=len(fields) + 1, column=0, columnspan=2, pady=8)
        tk.Button(window, text="Close", command=window.destroy, bg="#1c2633", fg="white", relief="flat", width=18).grid(row=len(fields) + 2, column=0, columnspan=2, pady=12)

    def _tracking_tick(self) -> None:
        if not self.tracking or self.camera is None:
            return
        if self.tracking_mode == "hand" and self.hand_tracker is None:
            return
        if self.tracking_mode in ("gaze", "double") and self.tracker is None:
            return
        frame = self.camera.read()
        if frame is not None and not self.paused:
            if self.tracking_mode in ("hand", "double"):
                hand = self.hand_tracker.process(frame) if self.hand_tracker is not None else None
                if hand is not None:
                    x, y, pinching, middle_pinching, middle_near, finger_count, fingers, palm_y = hand
                    previous_gesture = self.hand_session.last_gesture
                    point = self.hand_session.update(x, y, pinching, finger_count, fingers, palm_y, middle_pinching, middle_near)
                    if self.tracking_mode == "double" and self.eye_gestures is not None and self.tracker is not None:
                        face_result = self.tracker.process(frame)
                        if face_result.face_detected:
                            eye_action = self.eye_gestures.update(face_result.features.left_ear, face_result.features.right_ear)
                            if eye_action:
                                self.hand_session._set_gesture(eye_action, time.monotonic())
                    finger_names = ", ".join(name for name, detected in zip(("thumb", "index", "middle", "ring", "pinky"), fingers) if detected) or "fist"
                    command = self.hand_session.active_gesture() or self._hand_command(fingers, pinching, middle_pinching)
                    self.status.set(f"Hand control | {finger_names} | {command}")
                    camera_frame = self.hand_tracker.last_frame if self.hand_tracker is not None else frame
                    self._draw_camera_text(camera_frame, f"Fingers: {finger_names}", (18, 32), (255, 255, 255))
                    self._draw_camera_text(camera_frame, f"Action: {command}", (18, 64), (80, 220, 255))
                    gesture_text = self.hand_session.last_gesture.lower()
                    if self.hand_session.last_gesture != previous_gesture and ("click" in gesture_text or "scroll" in gesture_text or "drag" in gesture_text):
                        if self.overlay is not None:
                            self.overlay.flash_click()
                    if self.overlay is not None:
                        self.overlay.show_at(point)
                elif self.overlay is not None:
                    self.overlay.hide()
                else:
                    camera_frame = self.hand_tracker.last_frame if self.hand_tracker is not None else frame
                    self._draw_camera_text(camera_frame, "Fingers: none", (18, 32), (255, 255, 255))
                    self._draw_camera_text(camera_frame, "Action: NO HAND", (18, 64), (80, 220, 255))
                cv2.imshow("Project IRIS Camera", self.hand_tracker.last_frame if self.hand_tracker is not None else frame)
                cv2.waitKey(1)
                self.root.after(10, self._tracking_tick)
                return
            result = self.tracker.process(frame)
            cv2.imshow("Project IRIS Camera", frame)
            cv2.waitKey(1)
            if result.face_detected and self.session is not None:
                point = self.session.update(result.features)
                if point is not None and self.overlay is not None:
                    self.overlay.show_at(point)
                if self.settings.debug:
                    raw = self.session.last_raw
                    smooth = self.session.last_smoothed
                    self.status.set(f"EAR {result.features.ear:.2f} | raw {raw.x:.0f},{raw.y:.0f} | smooth {smooth.x:.0f},{smooth.y:.0f} | {self.session.blink_detector.last_state} | {self.session.last_action}")
            elif self.overlay is not None:
                self.overlay.hide()
        self.root.after(10, self._tracking_tick)

    @staticmethod
    def _hand_command(fingers: tuple[bool, ...], pinching: bool, middle_pinching: bool = False) -> str:
        if middle_pinching:
            return "NO HAND RIGHT-CLICK COMMAND"
        if pinching:
            return "PINCH HOLD TO DRAG"
        if len(fingers) >= 5 and all(fingers):
            return "SWIPE TO SWITCH DESKTOP"
        if len(fingers) >= 4 and fingers[1] and fingers[2] and not any(fingers[3:]):
            return "SCROLL UP/DOWN"
        if len(fingers) >= 2 and fingers[1] and not any(fingers[2:]):
            return "MOVE CURSOR"
        if not any(fingers):
            return "FIST CLICK"
        return "NO COMMAND"

    @staticmethod
    def _draw_camera_text(frame, text: str, position: tuple[int, int], color: tuple[int, int, int]) -> None:
        cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 5, cv2.LINE_AA)
        cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2, cv2.LINE_AA)

    def stop_tracking(self) -> None:
        self.tracking = False
        if self.overlay is not None:
            self.overlay.close()
            self.overlay = None
        if self.session is not None:
            self.session.mouse.enabled = False
        if hasattr(self, "hand_session"):
            self.hand_session.cancel_drag()
            self.hand_session.mouse.enabled = False
        try:
            cv2.destroyWindow("Project IRIS Camera")
        except cv2.error:
            cv2.destroyAllWindows()
        self.status.set("Tracking stopped. Preview mode is safe to test.")

    def toggle_pause(self) -> None:
        if self.session is not None:
            self.paused = not self.paused
            self.session.paused = self.paused
            self.status.set("Tracking paused." if self.paused else "Tracking resumed.")

    def close(self) -> None:
        self.stop_tracking()
        if self.tracker is not None:
            self.tracker.close()
        if self.hand_tracker is not None:
            self.hand_tracker.close()
        if self.camera is not None:
            self.camera.close()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    EyeMouseApp().run()
