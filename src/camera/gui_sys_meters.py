"""Slim full-height stack of RAM / CPU / GPU0-VRAM meters."""

from __future__ import annotations

import tkinter as tk
from typing import List, Optional, Sequence, Tuple

from src.camera.gui_theme import BORDER, FONT_FAMILY, MUTED, SURFACE_2, TEXT
from src.camera.sys_usage import as_triplet, sample_sys_usage

METER_WIDTH = 48
_POLL_MS = 500
_OK = "#2f9e6b"
_WARN = "#c9a227"
_HOT = "#c45c4a"
_NAMES = ("RAM", "CPU", "VRAM")


def _color(pct: Optional[float]) -> str:
    if pct is None:
        return BORDER
    if pct < 60.0:
        return _OK
    if pct < 85.0:
        return _WARN
    return _HOT


def _pct_text(pct: Optional[float]) -> str:
    return "—" if pct is None else f"{int(round(pct))}%"


class SysUsageStrip:
    """Three equal-height vertical fill bars with name + % overlay."""

    def __init__(self, parent: tk.Misc) -> None:
        self.frame = tk.Frame(
            parent, bg=SURFACE_2, width=METER_WIDTH,
            highlightthickness=1, highlightbackground=BORDER,
        )
        self.frame.columnconfigure(0, weight=1)
        self._canvases: List[tk.Canvas] = []
        self._values: List[Optional[float]] = [None, None, None]
        self._job: Optional[str] = None
        self._root: Optional[tk.Misc] = None
        for i in range(3):
            self.frame.rowconfigure(i, weight=1, uniform="sysm")
            c = tk.Canvas(
                self.frame, bg=SURFACE_2, highlightthickness=0,
                width=METER_WIDTH, bd=0,
            )
            c.grid(row=i, column=0, sticky="nsew")
            c.bind("<Configure>", lambda _e, idx=i: self._paint(idx))
            self._canvases.append(c)

    def start(self, root: tk.Misc) -> None:
        self._root = root
        # Keep a Python ref so the after() loop is not GC'd.
        setattr(root, "_sys_usage_strip", self)
        self._tick()

    def stop(self) -> None:
        if self._job is not None and self._root is not None:
            try:
                self._root.after_cancel(self._job)
            except tk.TclError:
                pass
        self._job = None

    def _tick(self) -> None:
        self.set_values(as_triplet(sample_sys_usage()))
        if self._root is not None:
            self._job = self._root.after(_POLL_MS, self._tick)

    def set_values(self, values: Sequence[Optional[float]]) -> None:
        trip: Tuple[Optional[float], ...] = tuple(values)[:3]
        while len(trip) < 3:
            trip = trip + (None,)
        self._values = list(trip)
        for i in range(3):
            self._paint(i)

    def _paint(self, idx: int) -> None:
        c = self._canvases[idx]
        pct = self._values[idx]
        w = max(c.winfo_width(), 1)
        h = max(c.winfo_height(), 1)
        c.delete("all")
        fill_h = 0 if pct is None else int(round(h * max(0.0, min(100.0, pct)) / 100.0))
        if fill_h > 0:
            c.create_rectangle(0, h - fill_h, w, h, fill=_color(pct), outline="")
        # Divider under each segment except the last.
        if idx < 2:
            c.create_line(0, h - 1, w, h - 1, fill=BORDER)
        c.create_text(
            w // 2, h // 2 - 10, text=_NAMES[idx], fill=MUTED,
            font=(FONT_FAMILY, 9, "bold"),
        )
        c.create_text(
            w // 2, h // 2 + 8, text=_pct_text(pct), fill=TEXT,
            font=(FONT_FAMILY, 11, "bold"),
        )
