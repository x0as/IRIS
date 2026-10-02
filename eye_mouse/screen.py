from __future__ import annotations

import tkinter as tk


def primary_screen_size() -> tuple[int, int]:
    root = tk.Tk()
    root.withdraw()
    size = (root.winfo_screenwidth(), root.winfo_screenheight())
    root.destroy()
    return size
