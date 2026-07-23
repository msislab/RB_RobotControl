"""Motion-parameter fields for the settings panel."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, List

from src.camera.gui_theme import FONT_LABEL


def build_motion_section(
    parent: tk.Misc,
    defaults: Dict[str, Any],
    lockable: List[tk.Widget],
) -> Dict[str, Any]:
    """Add Motion card widgets; return dict of tk variables / accessors."""
    motion = ttk.LabelFrame(parent, text="Motion", style="Card.TLabelframe")
    motion.pack(fill=tk.X, pady=(0, 6))

    grid = ttk.Frame(motion, style="Surface.TFrame")
    grid.pack(fill=tk.X)

    def _float(r: int, c: int, label: str, key: str, default: float) -> tk.DoubleVar:
        cell = ttk.Frame(grid, style="Surface.TFrame")
        cell.grid(row=r, column=c, sticky="ew", padx=(0, 6), pady=2)
        grid.columnconfigure(c, weight=1)
        ttk.Label(cell, text=label, style="Muted.TLabel", font=FONT_LABEL).pack(anchor=tk.W)
        var = tk.DoubleVar(value=float(defaults.get(key, default)))
        e = ttk.Entry(cell, textvariable=var, width=12)
        e.pack(fill=tk.X, pady=(2, 0))
        lockable.append(e)
        return var

    ttk.Label(
        motion, text="Speed bar (scales move_speed_l)", style="Muted.TLabel", font=FONT_LABEL
    ).pack(anchor=tk.W)
    bar_row = ttk.Frame(motion, style="Surface.TFrame")
    bar_row.pack(fill=tk.X, pady=(0, 4))
    speed_bar = tk.DoubleVar(value=float(defaults.get("speed_bar", 1.0)))
    bar_lbl = tk.StringVar(value=f"{int(speed_bar.get() * 100)}%")

    def _on_bar(v: str) -> None:
        n = max(0.05, min(1.0, float(v)))
        n = round(n * 20) / 20
        speed_bar.set(n)
        bar_lbl.set(f"{int(n * 100)}%")

    sc = ttk.Scale(bar_row, from_=0.05, to=1.0, orient=tk.HORIZONTAL, command=_on_bar)
    sc.set(speed_bar.get())
    sc.pack(side=tk.LEFT, fill=tk.X, expand=True)
    ttk.Label(bar_row, textvariable=bar_lbl, width=5, style="Surface.TLabel").pack(
        side=tk.LEFT, padx=(8, 0)
    )
    lockable.append(sc)

    offset = _float(0, 0, "Offset (mm/s)", "offset", 600.0)
    time_step = _float(0, 1, "Time step (s)", "time_step", 0.1)
    t1 = _float(1, 0, "t1 (s)", "t1", 0.08)
    t2 = _float(1, 1, "t2 (s)", "t2", 0.03)
    gain = _float(2, 0, "gain", "gain", 0.5)
    alpha = _float(2, 1, "alpha", "alpha", 0.05)

    ttk.Label(
        motion, text="Home TCP", style="Muted.TLabel", font=FONT_LABEL
    ).pack(anchor=tk.W, pady=(2, 0))
    home_grid = ttk.Frame(motion, style="Surface.TFrame")
    home_grid.pack(fill=tk.X, pady=(0, 2))
    home_default = list(defaults.get("home", [-300.0, -450.0, 350.0, 90.0, 0.0, 0.0]))
    while len(home_default) < 6:
        home_default.append(0.0)
    home_vars: List[tk.DoubleVar] = []
    for i, name in enumerate(("x", "y", "z", "rx", "ry", "rz")):
        r, c = divmod(i, 3)
        cell = ttk.Frame(home_grid, style="Surface.TFrame")
        cell.grid(row=r, column=c, sticky="ew", padx=(0, 6), pady=2)
        home_grid.columnconfigure(c, weight=1)
        ttk.Label(cell, text=name, style="Muted.TLabel", font=FONT_LABEL).pack(anchor=tk.W)
        var = tk.DoubleVar(value=float(home_default[i]))
        e = ttk.Entry(cell, textvariable=var, width=10)
        e.pack(fill=tk.X, pady=(2, 0))
        lockable.append(e)
        home_vars.append(var)

    z_var = _float(3, 0, "Approach Z", "z", 350.0)

    return {
        "speed_bar": speed_bar,
        "offset": offset,
        "time_step": time_step,
        "t1": t1,
        "t2": t2,
        "gain": gain,
        "alpha": alpha,
        "home_vars": home_vars,
        "z": z_var,
        # Still applied on Start from config.yaml (not shown in GUI).
        "joint_speed": float(defaults.get("joint_speed", 180.0)),
        "joint_acc": float(defaults.get("joint_acc", 180.0)),
        "linear_speed": float(defaults.get("linear_speed", 1000.0)),
        "linear_acc": float(defaults.get("linear_acc", 1000.0)),
    }


def home_from_vars(home_vars: List[tk.DoubleVar]) -> list:
    return [float(v.get()) for v in home_vars]
