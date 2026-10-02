from __future__ import annotations

import time
import tkinter as tk

from .models import GazePoint


class GazeOverlay:
    def __init__(self, size: int = 18, opacity: float = 0.9) -> None:
        self.root = tk.Toplevel()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", opacity)
        self.root.configure(bg="magenta")
        self.root.attributes("-transparentcolor", "magenta")
        self.canvas = tk.Canvas(self.root, width=size * 2, height=size * 2, bg="magenta", highlightthickness=0)
        self.canvas.pack()
        self.circle = self.canvas.create_oval(4, 4, size * 2 - 4, size * 2 - 4, fill="magenta", outline="#ff4d6d", width=2)
        self.size = size
        self._clicked_until = 0.0
        self.hide()

    def show_at(self, point: GazePoint) -> None:
        self.canvas.itemconfigure(self.circle, fill="#ff4d6d" if time.monotonic() < self._clicked_until else "magenta")
        self.root.geometry(f"{self.size * 2}x{self.size * 2}+{round(point.x - self.size)}+{round(point.y - self.size)}")
        self.root.deiconify()
        self.root.lift()

    def flash_click(self, duration: float = 0.25) -> None:
        self._clicked_until = time.monotonic() + duration

    def hide(self) -> None:
        self.root.withdraw()

    def close(self) -> None:
        self.root.destroy()
