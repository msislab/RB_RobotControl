"""Build main window chrome: header, sidebar, preview, status."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, Tuple

from src.camera.gui_settings import SettingsPanel
from src.camera.gui_theme import SIDEBAR_WIDTH, SURFACE_2, apply_density


def build_main_layout(
    root: tk.Tk,
    style: ttk.Style,
    defaults: Dict[str, Any],
    on_start,
    on_stop,
) -> Tuple[
    SettingsPanel,
    ttk.Button,
    ttk.Button,
    tk.StringVar,
    ttk.Frame,
    Dict,
    Dict,
    Callable[[], None],
]:
    """Return settings, buttons, status, preview panel/maps, and a fit() callback."""
    apply_density(style, 1.0)

    header = ttk.Frame(root, padding=(12, 8))
    header.pack(side=tk.TOP, fill=tk.X)
    ttk.Label(header, text="RobotControl", style="Title.TLabel").pack(side=tk.LEFT)
    ttk.Label(header, text="  RealSense · live control", style="TLabel").pack(
        side=tk.LEFT, padx=(8, 0)
    )

    body = ttk.Frame(root, padding=(12, 0, 12, 8))
    body.pack(fill=tk.BOTH, expand=True)
    body.columnconfigure(0, minsize=SIDEBAR_WIDTH)
    body.columnconfigure(1, weight=1)
    body.rowconfigure(0, weight=1)

    # Top-align sidebar so Start/Stop sit under settings (no dead gap).
    left = ttk.Frame(body, style="Surface.TFrame", padding=10)
    left.grid(row=0, column=0, sticky="nw", padx=(0, 12))

    settings = SettingsPanel(left, defaults)
    settings.frame.pack(side=tk.TOP, fill=tk.X)

    actions = ttk.Frame(left, style="Surface.TFrame")
    actions.pack(side=tk.TOP, fill=tk.X, pady=(10, 0))
    start_btn = ttk.Button(actions, text="Start", style="Start.TButton", command=on_start)
    start_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
    stop_btn = ttk.Button(
        actions, text="Stop", style="Stop.TButton", command=on_stop, state=tk.DISABLED
    )
    stop_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

    right = ttk.Frame(body, style="Surface.TFrame", padding=10)
    right.grid(row=0, column=1, sticky="nsew")
    ttk.Label(right, text="Camera preview", style="Muted.TLabel").pack(anchor=tk.W)
    panel = ttk.Frame(right, style="Surface.TFrame")
    panel.pack(fill=tk.BOTH, expand=True, pady=(6, 0))
    labels: Dict[str, tk.Label] = {}
    frames: Dict[str, ttk.LabelFrame] = {}
    for key, title in (
        ("color", "RGB"),
        ("depth", "Depth"),
        ("ir1", "IR1"),
        ("ir2", "IR2"),
        ("stereo_depth", "Stereo depth"),
    ):
        fr = ttk.LabelFrame(panel, text=title, style="Preview.TLabelframe")
        lbl = tk.Label(fr, bg=SURFACE_2, fg="#8b97a8", text="—")
        lbl.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        labels[key] = lbl
        frames[key] = fr

    status = ttk.Frame(root, style="Surface.TFrame", padding=(12, 8))
    status.pack(side=tk.BOTTOM, fill=tk.X)
    status_var = tk.StringVar(value="Ready — edit settings, then Start")
    ttk.Label(status, textvariable=status_var, style="Status.TLabel").pack(anchor=tk.W)

    def fit(_event=None) -> None:
        # Keep readable fixed density; layout is top-packed (no stretch gap).
        apply_density(style, 1.0)

    root.after(50, fit)
    return settings, start_btn, stop_btn, status_var, panel, labels, frames, fit
