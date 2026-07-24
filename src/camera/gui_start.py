"""Background camera bring-up for the Tk Start button."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from src.camera.omron_camera import OmronCameras
from src.camera.realsense_camera import RealSenseCamera


def validate_start(cfg: Dict[str, Any]) -> Optional[str]:
    """Return an error message if nothing is enabled, else None."""
    want_robot = bool(cfg.get("robot_enabled", True))
    want_cam = bool(cfg.get("camera_enabled") or cfg.get("omron_enabled"))
    if not want_robot and not want_cam:
        return "Enable robot and/or a camera"
    return None


def start_cameras(
    cfg: Dict[str, Any],
    *,
    fps: int,
    serial: Optional[str],
) -> Tuple[Optional[RealSenseCamera], Optional[OmronCameras], List[str]]:
    """Open enabled backends in parallel. Raises on hard failure after cleanup."""
    cam: Optional[RealSenseCamera] = None
    om: Optional[OmronCameras] = None
    want_rs = bool(cfg.get("camera_enabled"))
    want_om = bool(cfg.get("omron_enabled"))

    def _start_rs() -> RealSenseCamera:
        c = RealSenseCamera(
            view=cfg["view"],
            fps=fps,
            serial=serial,
            width=cfg["width"],
            height=cfg["height"],
            exposure=cfg["camera_exposure"],
            gain=cfg["camera_gain"],
        )
        c.start()
        return c

    def _start_om() -> OmronCameras:
        o = OmronCameras(
            exposure=cfg["omron_exposure"],
            gain=cfg["omron_gain"],
        )
        o.start()
        return o

    try:
        if want_rs and want_om:
            with ThreadPoolExecutor(max_workers=2) as pool:
                f_rs = pool.submit(_start_rs)
                f_om = pool.submit(_start_om)
                cam = f_rs.result()
                om = f_om.result()
        elif want_rs:
            cam = _start_rs()
        elif want_om:
            om = _start_om()
        return cam, om, (om.camera_ids if om is not None else [])
    except Exception:
        if cam is not None:
            cam.stop()
        if om is not None:
            om.stop()
        logger.exception("Camera start failed")
        raise
