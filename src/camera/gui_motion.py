"""Motion-parameter fields for the settings panel."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, List

from src.camera.gui_theme import FONT_LABEL

_MULT_CHOICES = (1.0, 1.5, 2.0)


def _snap_mult(value: Any, default: float = 1.0) -> float:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return default
    return min(_MULT_CHOICES, key=lambda x: abs(x - v))


def _mult_radios(
    parent: tk.Misc,
    title: str,
    key: str,
    defaults: Dict[str, Any],
    lockable: List[tk.Widget],
) -> tk.DoubleVar:
    ttk.Label(parent, text=title, style="Muted.TLabel", font=FONT_LABEL).pack(anchor=tk.W)
    var = tk.DoubleVar(value=_snap_mult(defaults.get(key, 1.0)))
    row = ttk.Frame(parent, style="Surface.TFrame")
    row.pack(fill=tk.X, pady=(0, 4))
    for val in _MULT_CHOICES:
        r = ttk.Radiobutton(row, text=str(val).rstrip("0").rstrip("."), variable=var, value=val)
        r.pack(side=tk.LEFT, padx=(0, 12))
        lockable.append(r)
    return var


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
        motion,
        text="Sequence / Move speeds (used by Sequence + MoveXB)",
        style="Muted.TLabel",
        font=FONT_LABEL,
    ).pack(anchor=tk.W)
    spd_grid = ttk.Frame(motion, style="Surface.TFrame")
    spd_grid.pack(fill=tk.X, pady=(0, 4))

    def _spd(r: int, c: int, label: str, key: str, default: float) -> tk.DoubleVar:
        cell = ttk.Frame(spd_grid, style="Surface.TFrame")
        cell.grid(row=r, column=c, sticky="ew", padx=(0, 6), pady=2)
        spd_grid.columnconfigure(c, weight=1)
        ttk.Label(cell, text=label, style="Muted.TLabel", font=FONT_LABEL).pack(anchor=tk.W)
        var = tk.DoubleVar(value=float(defaults.get(key, default)))
        e = ttk.Entry(cell, textvariable=var, width=12)
        e.pack(fill=tk.X, pady=(2, 0))
        lockable.append(e)
        return var

    joint_speed = _spd(0, 0, "Joint speed (deg/s)", "joint_speed", 180.0)
    joint_acc = _spd(0, 1, "Joint acc (deg/s²)", "joint_acc", 180.0)
    linear_speed = _spd(1, 0, "Linear speed (mm/s)", "linear_speed", 1000.0)
    linear_acc = _spd(1, 1, "Linear acc (mm/s²)", "linear_acc", 1000.0)

    speed_mult = _mult_radios(
        motion, "Speed multiplier", "speed_multiplier", defaults, lockable
    )
    acc_mult = _mult_radios(
        motion, "Acc multiplier", "acceleration_multiplier", defaults, lockable
    )

    ttk.Label(
        motion, text="Speed bar (global; also scales ZigZag)", style="Muted.TLabel", font=FONT_LABEL
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

    return {
        "speed_bar": speed_bar,
        "offset": offset,
        "time_step": time_step,
        "home_vars": home_vars,
        "joint_speed": joint_speed,
        "joint_acc": joint_acc,
        "linear_speed": linear_speed,
        "linear_acc": linear_acc,
        "speed_multiplier": speed_mult,
        "acceleration_multiplier": acc_mult,
        # ZigZag-only defaults (not shown in menu) — from motion.yaml via defaults.
        "t1": float(defaults.get("t1", 0.08)),
        "t2": float(defaults.get("t2", 0.03)),
        "gain": float(defaults.get("gain", 0.5)),
        "alpha": float(defaults.get("alpha", 0.05)),
        "z": float(defaults.get("z", 350.0)),
    }


def home_from_vars(home_vars: List[tk.DoubleVar]) -> list:
    return [float(v.get()) for v in home_vars]
