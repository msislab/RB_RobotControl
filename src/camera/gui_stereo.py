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
        "max_disparity": int(cfg.get("stereo_max_disparity", 192)),
        "z_far": float(cfg.get("stereo_z_far", 1.0)),
        "onnx_size": str(cfg.get("stereo_onnx_size", "320x736")),
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


def reveal_stereo_pane(gui: Any) -> None:
    """Show stereo_depth cell and start its pane worker (Tk thread)."""
    if getattr(gui, "_stereo_pane", False):
        return
    gui._stereo_pane = True
    cfg = getattr(gui, "_start_cfg", {}) or {}
    omron_ids = list(gui.omron.camera_ids) if gui.omron is not None else []
    keys = rs_keys(cfg.get("view", "rgb"), gui.camera is not None, True) + omron_ids
    show_keys(gui.panel, gui._frames, gui._labels, keys)
    pool = getattr(gui, "_pane_workers", None)
    if pool is not None:
        pool.add_key("stereo_depth")
    gui.status_var.set("Running · stereo depth ready")
