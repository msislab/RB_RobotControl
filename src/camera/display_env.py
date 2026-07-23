"""Resolve a usable X11 DISPLAY for Tkinter, or fail clearly."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional


def _try_display(display: str) -> bool:
    """Return True if Tk can open on ``display``."""
    prev = os.environ.get("DISPLAY")
    os.environ["DISPLAY"] = display
    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        root.destroy()
        return True
    except Exception:
        if prev is None:
            os.environ.pop("DISPLAY", None)
        else:
            os.environ["DISPLAY"] = prev
        return False


def _candidates_from_x11_unix() -> List[str]:
    """Map ``/tmp/.X11-unix/XN`` → ``:N`` (highest first — often the active seat)."""
    sock_dir = Path("/tmp/.X11-unix")
    if not sock_dir.is_dir():
        return []
    nums: List[int] = []
    for path in sock_dir.iterdir():
        name = path.name
        if name.startswith("X") and name[1:].isdigit():
            nums.append(int(name[1:]))
    nums.sort(reverse=True)
    return [f":{n}" for n in nums]


def ensure_display() -> str:
    """Pick a working DISPLAY; set ``os.environ['DISPLAY']``.

    Order: current ``DISPLAY`` (if set) → sockets under ``/tmp/.X11-unix``.
    Raises ``SystemExit`` if none work.
    """
    tried: List[str] = []
    current = os.environ.get("DISPLAY")
    candidates: List[str] = []
    if current:
        candidates.append(current)
    for c in _candidates_from_x11_unix():
        if c not in candidates:
            candidates.append(c)

    for display in candidates:
        tried.append(display)
        if _try_display(display):
            os.environ["DISPLAY"] = display
            return display

    tried_msg = ", ".join(tried) if tried else "(none found)"
    raise SystemExit(
        "No usable display for Tkinter GUI. "
        f"Tried: {tried_msg}. "
        "Set DISPLAY (e.g. export DISPLAY=:1) or run on a desktop session."
    )
