"""Tk settings panel for robot + camera (applied on Start)."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, List, Optional

from src.camera.gui_camera import build_camera_section, camera_values
from src.camera.gui_motion import build_motion_section, home_from_vars
from src.camera.gui_focus import bind_release_focus, release_focus
from src.camera.gui_theme import FONT_LABEL
from src.config.ket_store import list_sequences


class SettingsPanel:
    """Build editable settings; geometry applied at Start; exposure/gain live."""

    def __init__(
        self,
        parent: tk.Misc,
        defaults: Dict[str, Any],
        *,
        on_live_change: Optional[Callable[[], None]] = None,
    ) -> None:
        self.frame = ttk.Frame(parent, style="Surface.TFrame")
        self._lockable: List[tk.Widget] = []
        d = defaults

        robot = ttk.LabelFrame(self.frame, text="Robot", style="Card.TLabelframe")
        robot.pack(fill=tk.X, pady=(0, 6))
        self.robot_en = tk.BooleanVar(value=bool(d.get("robot_enabled", True)))
        cb = ttk.Checkbutton(robot, text="Enable Robot", variable=self.robot_en)
        cb.pack(anchor=tk.W, pady=(0, 2))
        self._lockable.append(cb)

        ttk.Label(robot, text="Routine", style="Muted.TLabel", font=FONT_LABEL).pack(
            anchor=tk.W
        )
        routine_row = ttk.Frame(robot, style="Surface.TFrame")
        routine_row.pack(fill=tk.X, pady=(0, 4))
        self.routine_var = tk.StringVar(
            value=str(d.get("robot_routine", "zigzag")).lower()
        )
        for label, val in (("ZigZag", "zigzag"), ("Sequence", "ket")):
            r = ttk.Radiobutton(
                routine_row,
                text=label,
                variable=self.routine_var,
                value=val,
                command=lambda: release_focus(self.frame),
            )
            r.pack(side=tk.LEFT, padx=(0, 12))
            self._lockable.append(r)

        ttk.Label(
            robot, text="Sequence file", style="Muted.TLabel", font=FONT_LABEL
        ).pack(anchor=tk.W)
        names = list_sequences() or ["ket"]
        cur = str(d.get("robot_sequence", "ket")).strip() or "ket"
        if cur not in names:
            names = sorted(set(names) | {cur})
        self.sequence_var = tk.StringVar(value=cur)
        self.sequence_box = ttk.Combobox(
            robot, textvariable=self.sequence_var, values=names, state="readonly"
        )
        self.sequence_box.pack(fill=tk.X, pady=(0, 8))
        bind_release_focus(self.sequence_box)
        self._lockable.append(self.sequence_box)
        self.sequence_loop = tk.BooleanVar(
            value=bool(d.get("robot_sequence_loop", False))
        )
        self.sequence_merge = tk.BooleanVar(
            value=bool(d.get("robot_sequence_merge", False))
        )
        # Side-by-side so vertical scroll/hit drift cannot toggle the wrong one.
        opt_row = ttk.Frame(robot, style="Surface.TFrame")
        opt_row.pack(fill=tk.X, pady=(0, 6))
        loop_cb = ttk.Checkbutton(
            opt_row, text="Loop sequence", variable=self.sequence_loop
        )
        loop_cb.pack(side=tk.LEFT, padx=(0, 16))
        merge_cb = ttk.Checkbutton(
            opt_row, text="Merge movements", variable=self.sequence_merge
        )
        merge_cb.pack(side=tk.LEFT)
        self._lockable.extend((loop_cb, merge_cb))

        ttk.Label(
            robot, text="Controller IP", style="Muted.TLabel", font=FONT_LABEL
        ).pack(anchor=tk.W)
        self.ip_var = tk.StringVar(value=str(d.get("robot_ip", "")))
        e = ttk.Entry(robot, textvariable=self.ip_var, width=22)
        e.pack(fill=tk.X, pady=(0, 4))
        self._lockable.append(e)

        ttk.Label(
            robot, text="Operation mode", style="Muted.TLabel", font=FONT_LABEL
        ).pack(anchor=tk.W)
        mode_row = ttk.Frame(robot, style="Surface.TFrame")
        mode_row.pack(fill=tk.X)
        self.mode_var = tk.StringVar(value=str(d.get("operation_mode", "Simulation")))
        for label, val in (("Simulation", "Simulation"), ("Real", "Real")):
            r = ttk.Radiobutton(mode_row, text=label, variable=self.mode_var, value=val)
            r.pack(side=tk.LEFT, padx=(0, 12))
            self._lockable.append(r)

        self._motion = build_motion_section(self.frame, d, self._lockable)
        self._cam = build_camera_section(
            self.frame, d, self._lockable, on_live_change=on_live_change
        )

        ttk.Label(
            self.frame,
            text="Geometry applies on Start. Exposure/gain apply live.",
            style="Muted.TLabel",
            font=FONT_LABEL,
        ).pack(anchor=tk.W, pady=(6, 0))

    def set_locked(self, locked: bool) -> None:
        state = tk.DISABLED if locked else tk.NORMAL
        for w in self._lockable:
            try:
                w.configure(state=state)
            except tk.TclError:
                pass

    def set_sequence(self, name: str) -> None:
        cur = str(name).strip() or "ket"
        names = list(self.sequence_box["values"]) or []
        if cur not in names:
            names = sorted(set(names) | {cur})
            self.sequence_box["values"] = names
        self.sequence_var.set(cur)

    def refresh_sequences(self) -> None:
        names = list_sequences() or ["ket"]
        cur = self.sequence_var.get().strip() or "ket"
        if cur not in names:
            names = sorted(set(names) | {cur})
        self.sequence_box["values"] = names
        self.sequence_var.set(cur)

    def values(self) -> Dict[str, Any]:
        m = self._motion
        out = {
            "robot_enabled": bool(self.robot_en.get()),
            "robot_routine": self.routine_var.get().strip().lower(),
            "robot_sequence": self.sequence_var.get().strip() or "ket",
            "robot_sequence_loop": bool(self.sequence_loop.get()),
            "robot_sequence_merge": bool(self.sequence_merge.get()),
            "robot_ip": self.ip_var.get().strip(),
            "operation_mode": self.mode_var.get(),
            "joint_speed": float(m["joint_speed"].get()),
            "joint_acc": float(m["joint_acc"].get()),
            "linear_speed": float(m["linear_speed"].get()),
            "linear_acc": float(m["linear_acc"].get()),
            "speed_multiplier": float(m["speed_multiplier"].get()),
            "acceleration_multiplier": float(m["acceleration_multiplier"].get()),
            "speed_bar": float(m["speed_bar"].get()),
            "offset": float(m["offset"].get()),
            "time_step": float(m["time_step"].get()),
            "t1": float(m["t1"]),
            "t2": float(m["t2"]),
            "gain": float(m["gain"]),
            "alpha": float(m["alpha"]),
            "home": home_from_vars(m["home_vars"]),
            "z": float(m["z"]),
        }
        out.update(camera_values(self._cam))
        return out
