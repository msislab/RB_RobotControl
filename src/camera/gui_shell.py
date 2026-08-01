"""Build main window chrome: header, sidebar, preview, status."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, Optional, Tuple

from src.camera.gui_scroll import scrollable_column
from src.camera.gui_settings import SettingsPanel
from src.camera.gui_sys_meters import METER_WIDTH, SysUsageStrip
from src.camera.gui_theme import (
    FONT_UI,
    MUTED,
    SIDEBAR_WIDTH,
    SURFACE_2,
    apply_density,
)


def add_preview_pane(
    panel: ttk.Frame,
    labels: Dict[str, tk.Label],
    frames: Dict[str, ttk.LabelFrame],
    key: str,
    title: str,
    titles: Optional[Dict[str, str]] = None,
) -> None:
    if key in frames:
        return
    fr = ttk.LabelFrame(panel, text=title, style="Preview.TLabelframe")
    lbl = tk.Label(fr, bg=SURFACE_2, fg=MUTED, text="—", font=FONT_UI)
    lbl.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
    labels[key] = lbl
    frames[key] = fr
    if titles is not None:
        titles[key] = title


def build_main_layout(
    root: tk.Tk,
    style: ttk.Style,
    defaults: Dict[str, Any],
    on_start,
    on_stop,
    *,
    on_immediate_stop: Optional[Callable[[], None]] = None,
    on_live_change: Optional[Callable[[], None]] = None,
    on_hide_preview: Optional[Callable[[bool], None]] = None,
    on_speed_bar_change: Optional[Callable[[float], None]] = None,
    on_open_robot: Optional[Callable[[], None]] = None,
) -> Tuple[
    SettingsPanel,
    ttk.Frame,
    ttk.Button,
    ttk.Button,
    ttk.Button,
    tk.StringVar,
    ttk.Frame,
    Dict,
    Dict,
    Dict,
    Callable[[], None],
]:
    """Return settings, scroll_inner, buttons, status, preview maps, titles, fit()."""
    apply_density(style, 1.0)

    header = ttk.Frame(root, padding=(12, 8))
    header.pack(side=tk.TOP, fill=tk.X)
    ttk.Label(header, text="RobotControl", style="Title.TLabel").pack(side=tk.LEFT)
    ttk.Label(header, text="  RealSense · Omron · live control", style="TLabel").pack(
        side=tk.LEFT, padx=(8, 0)
    )

    body = ttk.Frame(root, padding=(12, 0, 12, 8))
    body.pack(fill=tk.BOTH, expand=True)
    body.columnconfigure(0, minsize=SIDEBAR_WIDTH)
    body.columnconfigure(1, weight=1)
    body.columnconfigure(2, minsize=METER_WIDTH)
    body.rowconfigure(0, weight=1)

    left = ttk.Frame(body, style="Surface.TFrame")
    left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
    left.rowconfigure(0, weight=1)
    left.columnconfigure(0, weight=1)

    scroll_inner = scrollable_column(left)
    settings = SettingsPanel(
        scroll_inner,
        defaults,
        on_live_change=on_live_change,
        on_hide_preview=on_hide_preview,
        on_speed_bar_change=on_speed_bar_change,
    )
    settings.frame.pack(side=tk.TOP, fill=tk.X)

    actions = ttk.Frame(left, style="Surface.TFrame", padding=(10, 0, 10, 10))
    actions.grid(row=1, column=0, sticky="ew")
    if on_open_robot is not None:
        ttk.Button(actions, text="Open robot controls", command=on_open_robot).pack(
            fill=tk.X, pady=(0, 8)
        )
    row = ttk.Frame(actions, style="Surface.TFrame")
    row.pack(fill=tk.X)
    start_btn = ttk.Button(row, text="Start", style="Start.TButton", command=on_start)
    start_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
    stop_btn = ttk.Button(
        row, text="Stop", style="Stop.TButton", command=on_stop, state=tk.DISABLED
    )
    stop_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
    immediate_btn = ttk.Button(
        actions,
        text="Immediate Stop",
        style="Stop.TButton",
        command=on_immediate_stop or on_stop,
        state=tk.DISABLED,
    )
    immediate_btn.pack(fill=tk.X, pady=(8, 0))

    right = ttk.Frame(body, style="Surface.TFrame", padding=10)
    right.grid(row=0, column=1, sticky="nsew")
    ttk.Label(right, text="Camera preview", style="Muted.TLabel").pack(anchor=tk.W)
    panel = ttk.Frame(right, style="Surface.TFrame")
    panel.pack(fill=tk.BOTH, expand=True, pady=(6, 0))
    labels: Dict[str, tk.Label] = {}
    frames: Dict[str, ttk.LabelFrame] = {}
    titles: Dict[str, str] = {}
    for key, title in (
        ("color", "RS RGB"),
        ("depth", "Depth"),
        ("ir1", "IR1"),
        ("ir2", "IR2"),
        ("stereo_depth", "Stereo depth"),
    ):
        add_preview_pane(panel, labels, frames, key, title, titles)

    meters = SysUsageStrip(body)
    meters.frame.grid(row=0, column=2, sticky="nsew", padx=(8, 0))
    meters.start(root)

    status = ttk.Frame(root, style="Surface.TFrame", padding=(12, 8))
    status.pack(side=tk.BOTTOM, fill=tk.X)
    status_var = tk.StringVar(value="Ready — edit settings, then Start")
    ttk.Label(status, textvariable=status_var, style="Status.TLabel").pack(anchor=tk.W)

    def fit(_event=None) -> None:
        apply_density(style, 1.0)

    root.after(50, fit)
    return (
        settings, scroll_inner, start_btn, stop_btn, immediate_btn, status_var,
        panel, labels, frames, titles, fit,
    )
