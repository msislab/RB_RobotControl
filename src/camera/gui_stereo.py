"""Stereo depth preview helpers (keys, worker lifecycle)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from loguru import logger

from src.camera.depth import StereoWorker
from src.utils.color import yellow


def preview_keys(view: str, camera_on: bool, stereo_on: bool) -> List[str]:
    keys: List[str] = []
    if camera_on:
        keys.append("color")
        if view in ("rgb_depth", "rgb_depth_ir"):
            keys.append("depth")
        if view == "rgb_depth_ir":
            keys.extend(["ir1", "ir2"])
    if stereo_on:
        keys.append("stereo_depth")
    return keys


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
