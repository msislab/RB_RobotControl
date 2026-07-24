"""Camera settings block (RealSense + Omron) for the Tk sidebar."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, List, Optional, Tuple

from src.camera.gui_theme import FONT_LABEL

FPS_STEPS: Tuple[int, ...] = (5, 15, 25, 30)
RS_EXP = (1, 10000)
RS_GAIN = (0, 128)
OM_EXP = (500, 20000)
OM_EXP_STEP = 500
# Sentech analog gain 0–20.8 dB → GenICam Gain often 0–208 (overridden by device probe).
OM_GAIN_DEFAULT = (0, 208)


def build_camera_section(
    parent: tk.Misc,
    defaults: Dict[str, Any],
    lockable: List[tk.Widget],
    *,
    on_live_change: Optional[Callable[[], None]] = None,
) -> Dict[str, Any]:
    """Build camera controls; returns vars dict used by SettingsPanel.values()."""
    d = defaults
    cam = ttk.LabelFrame(parent, text="Camera", style="Card.TLabelframe")
    cam.pack(fill=tk.X)

    rs_en = tk.BooleanVar(value=bool(d.get("camera_enabled", True)))
    om_en = tk.BooleanVar(value=bool(d.get("omron_enabled", False)))
    for text, var in (("Enable RealSense", rs_en), ("Enable Omron", om_en)):
        cb = ttk.Checkbutton(cam, text=text, variable=var)
        cb.pack(anchor=tk.W, pady=(0, 2))
        lockable.append(cb)

    fps0 = int(d.get("fps", 30))
    idx = FPS_STEPS.index(fps0) if fps0 in FPS_STEPS else len(FPS_STEPS) - 1
    fps_idx = tk.IntVar(value=idx)
    fps_lbl = tk.StringVar(value=str(FPS_STEPS[idx]))
    ttk.Label(cam, text="FPS", style="Muted.TLabel", font=FONT_LABEL).pack(anchor=tk.W)
    fps_row = ttk.Frame(cam, style="Surface.TFrame")
    fps_row.pack(fill=tk.X, pady=(0, 4))

    def _on_fps(value: str) -> None:
        i = max(0, min(len(FPS_STEPS) - 1, int(round(float(value)))))
        fps_idx.set(i)
        fps_lbl.set(str(FPS_STEPS[i]))

    sc = ttk.Scale(fps_row, from_=0, to=len(FPS_STEPS) - 1, orient=tk.HORIZONTAL, command=_on_fps)
    sc.set(idx)
    sc.pack(side=tk.LEFT, fill=tk.X, expand=True)
    ttk.Label(fps_row, textvariable=fps_lbl, width=4, style="Surface.TLabel").pack(
        side=tk.LEFT, padx=(8, 0)
    )
    lockable.append(sc)

    ttk.Label(cam, text="View mode (RealSense)", style="Muted.TLabel", font=FONT_LABEL).pack(
        anchor=tk.W
    )
    view_row = ttk.Frame(cam, style="Surface.TFrame")
    view_row.pack(fill=tk.X, pady=(0, 4))
    view_var = tk.StringVar(value=str(d.get("view", "rgb")))
    for value, label in (
        ("rgb", "RGB"),
        ("rgb_depth", "RGB+Depth"),
        ("rgb_depth_ir", "RGB+Depth+IR"),
    ):
        r = ttk.Radiobutton(view_row, text=label, variable=view_var, value=value)
        r.pack(side=tk.LEFT, padx=(0, 8))
        lockable.append(r)

    rs_exp = tk.DoubleVar(value=float(d.get("camera_exposure", 100)))
    rs_gain = tk.DoubleVar(value=float(d.get("camera_gain", 16)))
    om0 = float(d.get("omron_exposure", 500))
    om0 = max(OM_EXP[0], min(OM_EXP[1], round(om0 / OM_EXP_STEP) * OM_EXP_STEP))
    om_exp = tk.DoubleVar(value=om0)
    om_g_lo = float(d.get("omron_gain_min", OM_GAIN_DEFAULT[0]))
    om_g_hi = float(d.get("omron_gain_max", OM_GAIN_DEFAULT[1]))
    om_g0 = max(om_g_lo, min(om_g_hi, float(d.get("omron_gain", 50))))
    om_gain = tk.DoubleVar(value=om_g0)
    live = on_live_change
    _scale_float(cam, "RealSense exposure", rs_exp, *RS_EXP, lockable, live=live)
    _scale_float(cam, "RealSense gain", rs_gain, *RS_GAIN, lockable, live=live)
    _scale_float(
        cam, "Omron exposure", om_exp, *OM_EXP, lockable, live=live, step=OM_EXP_STEP
    )
    _scale_float(cam, "Omron gain", om_gain, om_g_lo, om_g_hi, lockable, live=live)

    return {
        "camera_enabled": rs_en,
        "omron_enabled": om_en,
        # RealSense stream size from camera.yaml (Omron uses sensor max ROI).
        "width": int(d.get("width", 640)),
        "height": int(d.get("height", 360)),
        "fps_idx": fps_idx,
        "view": view_var,
        "camera_exposure": rs_exp,
        "camera_gain": rs_gain,
        "omron_exposure": om_exp,
        "omron_gain": om_gain,
    }


def camera_values(cam: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "camera_enabled": bool(cam["camera_enabled"].get()),
        "omron_enabled": bool(cam["omron_enabled"].get()),
        "width": int(cam["width"]),
        "height": int(cam["height"]),
        "fps": FPS_STEPS[int(cam["fps_idx"].get())],
        "view": cam["view"].get(),
        "camera_exposure": float(cam["camera_exposure"].get()),
        "camera_gain": float(cam["camera_gain"].get()),
        "omron_exposure": float(cam["omron_exposure"].get()),
        "omron_gain": float(cam["omron_gain"].get()),
    }


def apply_live_exposure(cfg: Dict[str, Any], camera: Any, omron: Any) -> None:
    if camera is not None:
        camera.set_exposure_gain(cfg["camera_exposure"], cfg["camera_gain"])
    if omron is not None:
        omron.set_exposure_gain(cfg["omron_exposure"], cfg["omron_gain"])


def _scale_float(
    parent,
    label,
    var,
    lo,
    hi,
    lockable,
    *,
    live: Optional[Callable[[], None]],
    step: float = 1,
) -> None:
    ttk.Label(parent, text=label, style="Muted.TLabel", font=FONT_LABEL).pack(anchor=tk.W)
    row = ttk.Frame(parent, style="Surface.TFrame")
    row.pack(fill=tk.X, pady=(0, 4))
    lbl = tk.StringVar(value=str(int(var.get())))

    def _on(v: str) -> None:
        n = max(lo, min(hi, float(v)))
        if step > 1:
            n = round(n / step) * step
            n = max(lo, min(hi, n))
        var.set(n)
        lbl.set(str(int(n)))
        if live is not None:
            live()

    sc = ttk.Scale(row, from_=lo, to=hi, orient=tk.HORIZONTAL, command=_on)
    sc.set(var.get())
    sc.pack(side=tk.LEFT, fill=tk.X, expand=True)
    ttk.Label(row, textvariable=lbl, width=6, style="Surface.TLabel").pack(
        side=tk.LEFT, padx=(8, 0)
    )
    # Live controls stay enabled while running — not added to lockable.
