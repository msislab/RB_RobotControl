"""Stereo depth preview helpers (keys, worker lifecycle)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from loguru import logger

from src.camera.depth import StereoWorker
from src.camera.gui_preview import rs_keys, show_keys
from src.utils.color import yellow


def preview_keys(view: str, camera_on: bool, stereo_on: bool) -> List[str]:
    return rs_keys(view, camera_on, stereo_on)


def stereo_cfg_from_settings(cfg: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "enabled": bool(cfg.get("stereo_enabled", False)),
        "backend": str(cfg.get("stereo_backend", "pytorch")),
        "variant": str(cfg.get("stereo_variant", "23-36-37")),
        "valid_iters": int(cfg.get("stereo_valid_iters", 4)),
        "z_far": float(cfg.get("stereo_z_far", 1.0)),
        "onnx_size": str(cfg.get("stereo_onnx_size", "576x960")),
    }


def start_stereo_worker(camera: Any, cfg: Dict[str, Any]) -> Optional[StereoWorker]:
    """Start async stereo worker; return None on soft-fail."""
    sc = stereo_cfg_from_settings(cfg)
    if not sc["enabled"]:
        return None
    cal = getattr(camera, "stereo_calibration", None)
    if not cal:
        logger.warning(yellow("Stereo: no IR calibration; skipping"))
        return None
    fx, baseline = cal
    worker = StereoWorker(
        fx,
        baseline,
        sc,
        width=int(cfg["width"]),
        height=int(cfg["height"]),
    )
    worker.start_load()
    return worker


def stop_stereo_worker(worker: Optional[StereoWorker]) -> None:
    if worker is not None:
        worker.stop()


def tick_stereo(gui: Any, frames: Dict[str, Any]) -> None:
    """Feed IR to worker; reveal stereo pane when ready; attach heatmap."""
    w = getattr(gui, "_stereo", None)
    if w is None:
        return
    if w.error and not getattr(gui, "_stereo_pane", False):
        gui.status_var.set(f"Stereo unavailable: {w.error}")
        return
    if w.ready and not getattr(gui, "_stereo_pane", False):
        gui._stereo_pane = True
        cfg = getattr(gui, "_start_cfg", {}) or {}
        omron_ids = list(gui.omron.camera_ids) if gui.omron is not None else []
        keys = rs_keys(cfg.get("view", "rgb"), gui.camera is not None, True) + omron_ids
        show_keys(gui.panel, gui._frames, gui._labels, keys)
        gui.status_var.set("Running · stereo depth ready")
    if w.ready and "ir1" in frames and "ir2" in frames:
        w.submit(frames["ir1"], frames["ir2"])
        heat = w.latest_heatmap()
        if heat is not None:
            frames["stereo_depth"] = heat
