from __future__ import annotations

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
        self.canvas.create_oval(4, 4, size * 2 - 4, size * 2 - 4, fill="#ff4d6d", outline="white", width=2)
        self.size = size
        self.hide()

    def show_at(self, point: GazePoint) -> None:
        self.root.geometry(f"{self.size * 2}x{self.size * 2}+{round(point.x - self.size)}+{round(point.y - self.size)}")
        self.root.deiconify()
        self.root.lift()

    def hide(self) -> None:
        self.root.withdraw()

    def close(self) -> None:
        self.root.destroy()
