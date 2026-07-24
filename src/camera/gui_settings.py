"""Tk settings panel for robot + camera (applied on Start)."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, List, Tuple

from src.camera.gui_motion import build_motion_section, home_from_vars
from src.camera.gui_theme import FONT_LABEL, MUTED, SURFACE

CAM_MIN = 240
CAM_MAX_W = 1280
CAM_MAX_H = 720
FPS_STEPS: Tuple[int, ...] = (5, 15, 25, 30)


class SettingsPanel:
    """Build editable settings; values applied only at Start."""

    def __init__(self, parent: tk.Misc, defaults: Dict[str, Any]) -> None:
        self.frame = ttk.Frame(parent, style="Surface.TFrame")
        self._lockable: List[tk.Widget] = []
        d = defaults

        robot = ttk.LabelFrame(self.frame, text="Robot", style="Card.TLabelframe")
        robot.pack(fill=tk.X, pady=(0, 6))
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

        cam = ttk.LabelFrame(self.frame, text="Camera", style="Card.TLabelframe")
        cam.pack(fill=tk.X)
        self.cam_enabled = tk.BooleanVar(value=bool(d.get("camera_enabled", True)))
        cb = ttk.Checkbutton(cam, text="Enable RealSense", variable=self.cam_enabled)
        cb.pack(anchor=tk.W, pady=(0, 4))
        self._lockable.append(cb)
        self.stereo_enabled = tk.BooleanVar(value=bool(d.get("stereo_enabled", False)))
        stereo_cb = ttk.Checkbutton(
            cam, text="Enable stereo depth", variable=self.stereo_enabled
        )
        stereo_cb.pack(anchor=tk.W, pady=(0, 4))
        self._lockable.append(stereo_cb)
        self._stereo_backend = str(d.get("stereo_backend", "pytorch"))
        self._stereo_variant = str(d.get("stereo_variant", "23-36-37"))
        self._stereo_valid_iters = int(d.get("stereo_valid_iters", 4))
        self._stereo_z_far = float(d.get("stereo_z_far", 1.0))
        self._stereo_onnx_size = str(d.get("stereo_onnx_size", "576x960"))

        self.width_var = tk.IntVar(value=int(d.get("width", 640)))
        self.height_var = tk.IntVar(value=int(d.get("height", 360)))
        self.width_lbl = tk.StringVar()
        self.height_lbl = tk.StringVar()
        self._scale_block(cam, "Width", self.width_var, CAM_MIN, CAM_MAX_W, self.width_lbl)
        self._scale_block(cam, "Height", self.height_var, CAM_MIN, CAM_MAX_H, self.height_lbl)

        fps0 = int(d.get("fps", 30))
        idx = FPS_STEPS.index(fps0) if fps0 in FPS_STEPS else len(FPS_STEPS) - 1
        self.fps_idx = tk.IntVar(value=idx)
        self.fps_lbl = tk.StringVar(value=str(FPS_STEPS[idx]))
        ttk.Label(cam, text="FPS", style="Muted.TLabel", font=FONT_LABEL).pack(anchor=tk.W)
        fps_row = ttk.Frame(cam, style="Surface.TFrame")
        fps_row.pack(fill=tk.X, pady=(0, 4))
        sc = ttk.Scale(fps_row, from_=0, to=len(FPS_STEPS) - 1, orient=tk.HORIZONTAL)
        sc.configure(command=self._on_fps)
        sc.set(idx)
        sc.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(fps_row, textvariable=self.fps_lbl, width=4, style="Surface.TLabel").pack(
            side=tk.LEFT, padx=(8, 0)
        )
        self._lockable.append(sc)

        ttk.Label(
            cam, text="View mode", style="Muted.TLabel", font=FONT_LABEL
        ).pack(anchor=tk.W)
        view_row = ttk.Frame(cam, style="Surface.TFrame")
        view_row.pack(fill=tk.X)
        self.view_var = tk.StringVar(value=str(d.get("view", "rgb")))
        for value, label in (
            ("rgb", "RGB"),
            ("rgb_depth", "RGB+Depth"),
            ("rgb_depth_ir", "RGB+Depth+IR"),
        ):
            r = ttk.Radiobutton(view_row, text=label, variable=self.view_var, value=value)
            r.pack(side=tk.LEFT, padx=(0, 8))
            self._lockable.append(r)

        ttk.Label(
            self.frame,
            text="Settings apply only when you press Start.",
            style="Muted.TLabel",
            font=FONT_LABEL,
        ).pack(anchor=tk.W, pady=(6, 0))
        self._surface = SURFACE
        self._muted = MUTED

    def _scale_block(
        self, parent: tk.Misc, label: str, var: tk.IntVar,
        lo: int, hi: int, lbl: tk.StringVar,
    ) -> None:
        ttk.Label(parent, text=label, style="Muted.TLabel", font=FONT_LABEL).pack(
            anchor=tk.W
        )
        row = ttk.Frame(parent, style="Surface.TFrame")
        row.pack(fill=tk.X, pady=(0, 4))
        lbl.set(str(var.get()))

        def _on(v: str, _var=var, _lbl=lbl) -> None:
            n = max(lo, min(hi, int(float(v))))
            n -= n % 8
            _var.set(n)
            _lbl.set(str(n))

        sc = ttk.Scale(row, from_=lo, to=hi, orient=tk.HORIZONTAL, command=_on)
        sc.set(var.get())
        sc.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(row, textvariable=lbl, width=5, style="Surface.TLabel").pack(
            side=tk.LEFT, padx=(8, 0)
        )
        self._lockable.append(sc)

    def _on_fps(self, value: str) -> None:
        idx = max(0, min(len(FPS_STEPS) - 1, int(round(float(value)))))
        self.fps_idx.set(idx)
        self.fps_lbl.set(str(FPS_STEPS[idx]))

    def set_locked(self, locked: bool) -> None:
        state = tk.DISABLED if locked else tk.NORMAL
        for w in self._lockable:
            try:
                w.configure(state=state)
            except tk.TclError:
                pass

    def values(self) -> Dict[str, Any]:
        m = self._motion
        return {
            "robot_ip": self.ip_var.get().strip(),
            "operation_mode": self.mode_var.get(),
            "joint_speed": float(m["joint_speed"]),
            "joint_acc": float(m["joint_acc"]),
            "linear_speed": float(m["linear_speed"]),
            "linear_acc": float(m["linear_acc"]),
            "speed_bar": float(m["speed_bar"].get()),
            "offset": float(m["offset"].get()),
            "time_step": float(m["time_step"].get()),
            "t1": float(m["t1"].get()),
            "t2": float(m["t2"].get()),
            "gain": float(m["gain"].get()),
            "alpha": float(m["alpha"].get()),
            "home": home_from_vars(m["home_vars"]),
            "z": float(m["z"].get()),
            "camera_enabled": bool(self.cam_enabled.get()),
            "stereo_enabled": bool(self.stereo_enabled.get()),
            "stereo_backend": self._stereo_backend,
            "stereo_variant": self._stereo_variant,
            "stereo_valid_iters": self._stereo_valid_iters,
            "stereo_z_far": self._stereo_z_far,
            "stereo_onnx_size": self._stereo_onnx_size,
            "width": int(self.width_var.get()),
            "height": int(self.height_var.get()),
            "fps": FPS_STEPS[int(self.fps_idx.get())],
            "view": self.view_var.get(),
        }
