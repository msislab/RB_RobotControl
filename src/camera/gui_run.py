"""Start/stop helpers for CameraControlGui (keeps display_gui ≤200 lines)."""

from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional

from loguru import logger

from src.camera.capture_pool import CapturePool
from src.camera.frame_hub import FrameHub
from src.camera.gui_preview import rs_keys, setup_start_preview
from src.camera.gui_shell import add_preview_pane
from src.camera.gui_start import start_cameras
from src.camera.gui_stereo import reveal_stereo_pane, start_stereo_worker, stop_stereo_worker
from src.camera.omron_camera import OmronCameras
from src.camera.pane_workers import PaneWorkerPool
from src.camera.realsense_camera import RealSenseCamera
from src.utils.color import green, yellow


def begin_start(gui: Any, cfg: Dict[str, Any]) -> None:
    gui._fps = int(cfg["fps"])
    gui._start_cfg = cfg
    gui._starting = True
    gui._stereo = None
    gui._stereo_pane = False
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
    gui._stereo = start_stereo_worker(cam, cfg) if cam is not None else None
    gui._starting, gui._running = False, True
    gui._rs_on, gui._omron_n = cam is not None, len(omron_ids)
    gui._fps_board.reset()
    gui._fps_board.note_titles(gui._pane_titles)
    setup_start_preview(
        gui.panel, gui._frames, gui._labels,
        view=cfg["view"], camera_on=cam is not None, omron_ids=omron_ids,
        titles=gui._pane_titles, add_pane=add_preview_pane, stereo_on=False,
    )
    start_preview_workers(gui, cfg, omron_ids)
    gui.status_var.set("Running…")
    logger.info(green(f"Start cfg={cfg} omron={omron_ids}"))
    if cfg.get("robot_enabled", True):
        gui._robot_thread = threading.Thread(target=gui._robot_worker, daemon=True)
        gui._robot_thread.start()
    else:
        logger.info(yellow("Robot disabled — cameras only"))


def start_preview_workers(gui: Any, cfg: Dict[str, Any], omron_ids: List[str]) -> None:
    hub = FrameHub()
    gui._frame_hub = hub

    def on_stereo_ready() -> None:
        gui.root.after(0, lambda: reveal_stereo_pane(gui))

    cap = CapturePool(hub)
    gui._capture_pool = cap
    cap.start(
        camera=gui.camera,
        omron=gui.omron,
        stereo=gui._stereo,
        target_fps=gui._fps,
        on_stereo_ready=on_stereo_ready,
    )

    def on_frame(key: str) -> None:
        gui._fps_board.tick_key(key, gui._frames, gui._fps)

    def hide_preview() -> bool:
        return bool(getattr(gui, "_hide_preview", False))

    def clear_image(key: str) -> None:
        lbl = gui._labels.get(key)
        if lbl is not None:
            lbl.configure(image="", text="—")
        gui._photo.pop(key, None)

    panes = PaneWorkerPool(
        hub,
        schedule=lambda fn: gui.root.after(0, fn),
        get_frames=lambda: gui._frames,
        get_labels=lambda: gui._labels,
        get_photo=lambda: gui._photo,
        on_frame=on_frame,
        hide_preview=hide_preview,
        clear_image=clear_image,
    )
    gui._pane_workers = panes
    keys = rs_keys(cfg["view"], gui.camera is not None, False) + list(omron_ids)
    panes.start(keys)


def stop_preview_workers(gui: Any) -> None:
    panes = getattr(gui, "_pane_workers", None)
    if panes is not None:
        panes.stop()
        gui._pane_workers = None
    cap = getattr(gui, "_capture_pool", None)
    if cap is not None:
        cap.stop()
        gui._capture_pool = None
    gui._frame_hub = None


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


def halt_stereo(gui: Any) -> None:
    stop_stereo_worker(getattr(gui, "_stereo", None))
    gui._stereo = None
    gui._stereo_pane = False
