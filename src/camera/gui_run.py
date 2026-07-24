"""Start/stop helpers for CameraControlGui (keeps display_gui ≤200 lines)."""

from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional

from loguru import logger

from src.camera.gui_preview import setup_start_preview
from src.camera.gui_shell import add_preview_pane
from src.camera.gui_start import start_cameras
from src.camera.omron_camera import OmronCameras
from src.camera.realsense_camera import RealSenseCamera
from src.utils.color import green, yellow


def begin_start(gui: Any, cfg: Dict[str, Any]) -> None:
    gui._fps = int(cfg["fps"])
    gui._start_cfg = cfg
    gui._starting = True
    gui.settings.set_locked(True)
    gui.start_btn.configure(state="disabled")
    gui.stop_btn.configure(state="normal")
    gui.status_var.set("Starting…")
    threading.Thread(target=camera_start_worker, args=(gui, cfg), daemon=True).start()


def camera_start_worker(gui: Any, cfg: Dict[str, Any]) -> None:
    try:
        cam, om, omron_ids = start_cameras(cfg, fps=gui._fps, serial=gui.serial)
    except Exception as e:
        gui.root.after(0, lambda err=e: on_camera_start_failed(gui, err))
        return
    gui.root.after(0, lambda: on_camera_start_ok(gui, cfg, cam, om, omron_ids))


def on_camera_start_failed(gui: Any, err: Exception) -> None:
    gui._starting = False
    gui._stop_cameras()
    gui.settings.set_locked(False)
    gui.start_btn.configure(state="normal")
    gui.stop_btn.configure(state="disabled")
    gui.status_var.set(f"Camera failed: {err}")


def on_camera_start_ok(
    gui: Any,
    cfg: Dict[str, Any],
    cam: Optional[RealSenseCamera],
    om: Optional[OmronCameras],
    omron_ids: List[str],
) -> None:
    if not gui._starting:
        if cam is not None:
            cam.stop()
        if om is not None:
            om.stop()
        return
    gui.camera, gui.omron = cam, om
    gui._starting, gui._running = False, True
    gui._rs_on, gui._omron_n = cam is not None, len(omron_ids)
    gui._fps_board.reset()
    gui._fps_board.note_titles(gui._pane_titles)
    setup_start_preview(
        gui.panel, gui._frames, gui._labels,
        view=cfg["view"], camera_on=cam is not None, omron_ids=omron_ids,
        titles=gui._pane_titles, add_pane=add_preview_pane,
    )
    gui.status_var.set("Running…")
    logger.info(green(f"Start cfg={cfg} omron={omron_ids}"))
    if cfg.get("robot_enabled", True):
        gui._robot_thread = threading.Thread(target=gui._robot_worker, daemon=True)
        gui._robot_thread.start()
    else:
        logger.info(yellow("Robot disabled — cameras only"))
    if cam is not None or om is not None:
        gui.root.after(1, gui._schedule_frame)


def finish_stop(gui: Any) -> None:
    """Stop cameras + motion loop; keep robot connection for teach/manual."""
    gui._halt_run()
    gui.settings.set_locked(False)
    gui.start_btn.configure(state="normal")
    gui.stop_btn.configure(state="disabled")
    if hasattr(gui, "robot_panel"):
        gui.robot_panel.sync_connect_btn()
    connected = getattr(gui.app, "_setup_done", False)
    gui.status_var.set(
        "Stopped — robot still connected" if connected else "Stopped — change settings, then Start"
    )
    logger.info(yellow("Stop requested (robot connection kept)"))
