"""Threaded robot connect for launch auto-connect and Connect button."""

from __future__ import annotations

import threading
from typing import Any, Dict, Optional

from loguru import logger

from src.utils.color import green, yellow


def schedule_launch_connect(gui: Any) -> None:
    """If Enable Robot is on at GUI ready, connect in background."""
    try:
        cfg = gui.settings.values()
    except Exception as e:
        gui.status_var.set(f"Bad settings (skip auto-connect): {e}")
        return
    if not cfg.get("robot_enabled", True):
        logger.info(yellow("Robot disabled — skip auto-connect at launch"))
        gui.status_var.set("Robot disabled — use Connect in robot controls")
        return
    begin_connect(gui, cfg, status_busy="Connecting robot…")


def begin_connect(
    gui: Any,
    cfg: Optional[Dict[str, Any]] = None,
    *,
    status_busy: str = "Connecting robot…",
) -> None:
    if getattr(gui, "_connecting", False):
        return
    if cfg is None:
        try:
            cfg = gui.settings.values()
        except Exception as e:
            gui.status_var.set(f"Bad settings: {e}")
            return
    gui._connecting = True
    if hasattr(gui, "robot_panel"):
        gui.robot_panel.sync_connect_btn()
    gui.status_var.set(status_busy)
    threading.Thread(target=_connect_worker, args=(gui, dict(cfg)), daemon=True).start()


def _connect_worker(gui: Any, cfg: Dict[str, Any]) -> None:
    try:
        gui.app.connect_with_settings(cfg)
        gui.root.after(0, lambda: _on_ok(gui))
    except Exception as e:
        logger.warning(yellow(f"Robot connect failed: {e}"))
        gui.root.after(0, lambda err=e: _on_fail(gui, err))


def _on_ok(gui: Any) -> None:
    gui._connecting = False
    if hasattr(gui, "robot_panel"):
        gui.robot_panel.sync_connect_btn()
    gui.status_var.set("Robot connected")
    logger.info(green("Robot connect OK"))


def _on_fail(gui: Any, err: Exception) -> None:
    gui._connecting = False
    if hasattr(gui, "robot_panel"):
        gui.robot_panel.sync_connect_btn()
    gui.status_var.set(f"Robot connect failed: {err}")
