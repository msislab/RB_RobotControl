"""Preview grid layout for equal-sized camera panes."""

from __future__ import annotations

import math
import tkinter as tk
from tkinter import ttk
from typing import Dict, Sequence


def show_preview_keys(
    panel: ttk.Frame,
    frames: Dict[str, ttk.LabelFrame],
    labels: Dict[str, tk.Label],
    keys: Sequence[str],
) -> None:
    for fr in frames.values():
        fr.grid_forget()
    n = len(keys)
    cols = 1 if n <= 1 else 2 if n <= 4 else math.ceil(math.sqrt(n))
    rows = 1 if n == 0 else math.ceil(n / cols)
    for r in range(max(rows, 2)):
        panel.rowconfigure(
            r,
            weight=1 if r < rows else 0,
            uniform="preview_r" if r < rows else "preview_r_x",
        )
    for c in range(max(cols, 2)):
        panel.columnconfigure(
            c,
            weight=1 if c < cols else 0,
            uniform="preview_c" if c < cols else "preview_c_x",
        )
    for i, key in enumerate(keys):
        frames[key].grid(row=i // cols, column=i % cols, sticky="nsew", padx=6, pady=4)
    active = set(keys)
    for key, lbl in labels.items():
        if key not in active:
            lbl.configure(image="", text="—")
