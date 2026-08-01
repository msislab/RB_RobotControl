"""Start/stop helpers for CameraControlGui (keeps display_gui ≤200 lines)."""

from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional

from loguru import logger

from src.camera.capture_pool import CapturePool
from src.camera.device_fps import DeviceMetaStore
from src.camera.frame_hub import FrameHub
from src.camera.gui_preview import rs_keys, setup_start_preview
from src.camera.gui_shell import add_preview_pane
from src.camera.gui_start import start_cameras
from src.camera.gui_stereo import reveal_stereo_pane, start_stereo_worker
from src.camera.omron_camera import OmronCameras
from src.camera.pane_workers import PaneWorkerPool
from src.camera.realsense_camera import RealSenseCamera
from src.utils.color import green, yellow


def begin_start(gui: Any, cfg: Dict[str, Any]) -> None:
    if getattr(gui, "_stopping", False) or getattr(gui, "_stop_phase", None):
        gui.status_var.set("Still stopping — wait for cycle/home, then Start")
        return
    gui._fps = int(cfg["fps"])
    gui._start_cfg = cfg
    gui._starting = True
    gui._stereo = None
    gui._stereo_pane = False
    gui.settings.set_locked(True)
    gui.start_btn.configure(state="disabled")
    gui.stop_btn.configure(state="normal")
    if hasattr(gui, "immediate_btn"):
        gui.immediate_btn.configure(state="normal")
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
    if hasattr(gui, "immediate_btn"):
        gui.immediate_btn.configure(state="disabled")
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
        if not _robot_worker_ready(gui):
            return
        gui._robot_thread = threading.Thread(target=gui._robot_worker, daemon=True)
        gui._robot_thread.start()
    else:
        logger.info(yellow("Robot disabled — cameras only"))


_ROBOT_JOIN_TIMEOUT_S = 3.0


def _robot_worker_ready(gui: Any) -> bool:
    """Join a leftover robot worker after Stop; abort Start if still busy."""
    prev = getattr(gui, "_robot_thread", None)
    if prev is None or not prev.is_alive():
        return True
    logger.info(yellow(f"Waiting up to {_ROBOT_JOIN_TIMEOUT_S:.0f}s for previous robot worker…"))
    prev.join(timeout=_ROBOT_JOIN_TIMEOUT_S)
    if not prev.is_alive():
        return True
    gui._halt_run()
    gui.settings.set_locked(False)
    gui.start_btn.configure(state="normal")
    gui.stop_btn.configure(state="disabled")
    if hasattr(gui, "immediate_btn"):
        gui.immediate_btn.configure(state="disabled")
    msg = "Previous robot worker still busy — Immediate Stop and retry"
    gui.status_var.set(msg)
    logger.warning(msg)
    return False


def start_preview_workers(gui: Any, cfg: Dict[str, Any], omron_ids: List[str]) -> None:
    hub = FrameHub()
    gui._frame_hub = hub
    store = DeviceMetaStore()
    gui._device_meta = store
    gui._fps_board.device_meta = store

    def on_stereo_ready() -> None:
        gui.root.after(0, lambda: reveal_stereo_pane(gui))

    cap = CapturePool(hub, device_meta=store)
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
