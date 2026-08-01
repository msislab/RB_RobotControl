"""Stop / teardown helpers (kept off display_gui and gui_run size budgets)."""

from __future__ import annotations

import threading
from typing import Any

from loguru import logger

from src.camera.gui_stereo import stop_stereo_worker
from src.utils.color import yellow


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
    gui._device_meta = None
    gui._fps_board.device_meta = None


def _set_stop_buttons(gui: Any, *, start: str, stop: str) -> None:
    gui.start_btn.configure(state=start)
    gui.stop_btn.configure(state=stop)
    if hasattr(gui, "immediate_btn"):
        gui.immediate_btn.configure(state=stop)


def finish_stop(gui: Any, *, immediate: bool = False) -> None:
    """Stop motion on Tk thread; tear down cameras/stereo off Tk (avoids freeze)."""
    if getattr(gui, "_stopping", False):
        return
    if not (gui._running or gui._starting):
        return
    gui._stopping = True
    gui._running = gui._starting = False
    _set_stop_buttons(gui, start="disabled", stop="disabled")
    gui.status_var.set("Immediate stop…" if immediate else "Stopping…")
    try:
        if immediate:
            gui.app.request_immediate_stop()
        else:
            gui.app.request_stop()
    except Exception as e:
        logger.warning("stop request failed: {}", e)

    def worker() -> None:
        try:
            gui._stop_cameras()
        except Exception as e:
            logger.error("Stop cameras error: {}", e)
        finally:
            gui.root.after(0, lambda: _finish_stop_ui(gui, immediate=immediate))

    threading.Thread(target=worker, name="gui-stop", daemon=True).start()


def _finish_stop_ui(gui: Any, *, immediate: bool = False) -> None:
    gui._stopping = False
    gui.settings.set_locked(False)
    _set_stop_buttons(gui, start="normal", stop="disabled")
    if hasattr(gui, "robot_panel"):
        gui.robot_panel.sync_connect_btn()
    connected = getattr(gui.app, "_setup_done", False)
    if immediate:
        msg = (
            "Immediate stop — robot still connected"
            if connected
            else "Immediate stop — change settings, then Start"
        )
    else:
        msg = (
            "Stopped — robot finishing cycle/home if needed"
            if connected
            else "Stopped — change settings, then Start"
        )
    gui.status_var.set(msg)
    logger.info(yellow(
        "Immediate stop requested" if immediate else "Graceful stop requested"
    ))


def halt_stereo(gui: Any) -> None:
    stop_stereo_worker(getattr(gui, "_stereo", None))
    gui._stereo = None
    gui._stereo_pane = False


def halt_run(gui: Any) -> None:
    """Sync halt (Start-fail / close). Prefer ``finish_stop`` from Stop buttons."""
    gui._running = gui._starting = False
    try:
        gui.app.request_immediate_stop()
    except Exception as e:
        logger.warning("request_immediate_stop failed: {}", e)
    gui._stop_cameras()


def on_stop(gui: Any) -> None:
    if gui._running or gui._starting or gui._stopping:
        finish_stop(gui, immediate=False)


def on_immediate_stop(gui: Any) -> None:
    if gui._running or gui._starting or gui._stopping:
        finish_stop(gui, immediate=True)
