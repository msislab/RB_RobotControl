"""Stop / teardown helpers (kept off display_gui and gui_run size budgets)."""

from __future__ import annotations

import threading
from typing import Any, Optional

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


def stop_phase(gui: Any) -> Optional[str]:
    """``None`` | ``\"graceful\"`` | ``\"immediate\"`` while a stop is in progress."""
    return getattr(gui, "_stop_phase", None)


def _set_buttons(
    gui: Any, *, start: str, stop: str, immediate: Optional[str] = None
) -> None:
    gui.start_btn.configure(state=start)
    gui.stop_btn.configure(state=stop)
    if hasattr(gui, "immediate_btn"):
        gui.immediate_btn.configure(
            state=stop if immediate is None else immediate
        )


def _ensure_stop_watch(gui: Any) -> None:
    """Join robot worker, then tear down cameras; Start enables only after."""
    if getattr(gui, "_stop_watch_started", False):
        return
    gui._stop_watch_started = True

    def worker() -> None:
        t = getattr(gui, "_robot_thread", None)
        if t is not None and t.is_alive():
            logger.info(yellow("Waiting for robot worker to finish stop…"))
            t.join()
        try:
            gui._stop_cameras()
        except Exception as e:
            logger.error("Stop cameras error: {}", e)
        finally:
            gui.root.after(0, lambda: _finish_stop_ui(gui))

    threading.Thread(target=worker, name="gui-stop-watch", daemon=True).start()


def finish_stop(gui: Any, *, immediate: bool = False) -> None:
    """Request stop; cameras stay up until the robot worker exits."""
    if immediate:
        _begin_immediate_stop(gui)
    else:
        _begin_graceful_stop(gui)


def _begin_graceful_stop(gui: Any) -> None:
    if stop_phase(gui) is not None:
        return
    if not (gui._running or gui._starting):
        return
    gui._stop_phase = "graceful"
    gui._stopping = True  # blocks Start until watch finishes
    gui._running = gui._starting = False
    # Start/Stop off; Immediate stays available for emergency escalate.
    _set_buttons(gui, start="disabled", stop="disabled", immediate="normal")
    gui.status_var.set("Stopping… finishing cycle (Immediate Stop still available)")
    try:
        gui.app.request_stop()
    except Exception as e:
        logger.warning("request_stop failed: {}", e)
    logger.info(yellow("Graceful stop requested — cameras stay until cycle ends"))
    _ensure_stop_watch(gui)


def _begin_immediate_stop(gui: Any) -> None:
    phase = stop_phase(gui)
    if phase == "immediate":
        return
    if phase is None and not (gui._running or gui._starting):
        return
    gui._stop_phase = "immediate"
    gui._stopping = True
    gui._running = gui._starting = False
    _set_buttons(gui, start="disabled", stop="disabled", immediate="disabled")
    gui.status_var.set("Immediate stop…")
    try:
        gui.app.request_immediate_stop()
    except Exception as e:
        logger.warning("request_immediate_stop failed: {}", e)
    logger.info(yellow("Immediate stop requested"))
    _ensure_stop_watch(gui)


def _finish_stop_ui(gui: Any) -> None:
    phase = stop_phase(gui) or "graceful"
    gui._stop_phase = None
    gui._stop_watch_started = False
    gui._stopping = False
    gui.settings.set_locked(False)
    _set_buttons(gui, start="normal", stop="disabled", immediate="disabled")
    if hasattr(gui, "robot_panel"):
        gui.robot_panel.sync_connect_btn()
    connected = getattr(gui.app, "_setup_done", False)
    if phase == "immediate":
        msg = (
            "Immediate stop — robot still connected"
            if connected
            else "Immediate stop — change settings, then Start"
        )
    else:
        msg = (
            "Stopped — robot still connected"
            if connected
            else "Stopped — change settings, then Start"
        )
    gui.status_var.set(msg)
    logger.info(yellow("Stop complete (cameras down, Start enabled)"))


def halt_stereo(gui: Any) -> None:
    stop_stereo_worker(getattr(gui, "_stereo", None))
    gui._stereo = None
    gui._stereo_pane = False


def halt_run(gui: Any) -> None:
    """Sync halt (Start-fail / close). Prefer ``finish_stop`` from Stop buttons."""
    gui._running = gui._starting = False
    gui._stop_phase = None
    gui._stop_watch_started = False
    gui._stopping = False
    try:
        gui.app.request_immediate_stop()
    except Exception as e:
        logger.warning("request_immediate_stop failed: {}", e)
    gui._stop_cameras()


def on_stop(gui: Any) -> None:
    if stop_phase(gui) is not None:
        return
    if gui._running or gui._starting:
        finish_stop(gui, immediate=False)


def on_immediate_stop(gui: Any) -> None:
    if stop_phase(gui) == "immediate":
        return
    if gui._running or gui._starting or stop_phase(gui) == "graceful":
        finish_stop(gui, immediate=True)
