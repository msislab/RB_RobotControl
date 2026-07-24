"""Place-based vertical scroll column (avoids Canvas first-click eat on X11)."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, Dict


def pointer_in(widget: tk.Misc, x_root: int, y_root: int) -> bool:
    """True if screen point lies inside widget's root bbox."""
    try:
        x0, y0 = widget.winfo_rootx(), widget.winfo_rooty()
        return (
            x0 <= x_root < x0 + widget.winfo_width()
            and y0 <= y_root < y0 + widget.winfo_height()
        )
    except tk.TclError:
        return False


def scrollable_column(parent: ttk.Frame) -> ttk.Frame:
    """
    Vertical scroll via place() — not Canvas create_window.

    Canvas-embedded controls on X11 often need a first click only to
    activate the window, so the real action needs a second click.
    """
    wrap = ttk.Frame(parent, style="Surface.TFrame")
    wrap.grid(row=0, column=0, sticky="nsew")
    wrap.rowconfigure(0, weight=1)
    wrap.columnconfigure(0, weight=1)

    clip = ttk.Frame(wrap, style="Surface.TFrame")
    clip.grid(row=0, column=0, sticky="nsew")
    clip.rowconfigure(0, weight=1)
    clip.columnconfigure(0, weight=1)

    sb = ttk.Scrollbar(wrap, orient=tk.VERTICAL)
    sb.grid(row=0, column=1, sticky="ns")

    inner = ttk.Frame(clip, style="Surface.TFrame", padding=10)
    inner.place(x=0, y=0, relwidth=1.0)
    state: Dict[str, Any] = {"y": 0.0, "job": None}

    def _max_scroll() -> int:
        return max(0, int(inner.winfo_reqheight()) - int(clip.winfo_height()))

    def _apply_y(y: float) -> None:
        top = _max_scroll()
        y = max(0.0, min(float(y), float(top)))
        state["y"] = y
        inner.place_configure(y=-int(y))
        if top <= 0:
            sb.set(0.0, 1.0)
        else:
            lo = y / top
            hi = (y + clip.winfo_height()) / max(1, inner.winfo_reqheight())
            sb.set(lo, min(1.0, hi))

    def _on_sb(*args) -> None:
        top = _max_scroll()
        if not args:
            return
        if args[0] == "moveto":
            _apply_y(float(args[1]) * top)
        elif args[0] == "scroll":
            steps = int(args[1])
            unit = args[2] if len(args) > 2 else "units"
            delta = steps * (clip.winfo_height() if unit == "pages" else 40)
            _apply_y(state["y"] + delta)

    sb.configure(command=_on_sb)

    def _sync(_event=None) -> None:
        _apply_y(state["y"])

    def _schedule_sync(_event=None) -> None:
        jid = state.get("job")
        if jid is not None:
            try:
                clip.after_cancel(jid)
            except tk.TclError:
                pass
        state["job"] = clip.after_idle(_sync)

    inner.bind("<Configure>", _schedule_sync)
    clip.bind("<Configure>", _schedule_sync)

    def _wheel(event: tk.Event) -> None:
        if not pointer_in(wrap, int(event.x_root), int(event.y_root)):
            return
        if getattr(event, "num", None) == 5 or getattr(event, "delta", 0) < 0:
            _apply_y(state["y"] + 40)
        else:
            _apply_y(state["y"] - 40)

    for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
        wrap.bind_all(seq, _wheel, add="+")
    return inner
