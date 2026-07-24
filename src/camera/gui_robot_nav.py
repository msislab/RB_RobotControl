"""Swap main settings ↔ robot control sidebar views."""

from __future__ import annotations

import tkinter as tk
from typing import Any, List


def home_pose(gui: Any) -> List[float]:
    try:
        return list(gui.settings.values()["home"])
    except Exception:
        return list(gui.defaults.get("home", [0, 0, 0, 0, 0, 0]))


def show_robot_controls(gui: Any) -> None:
    if gui._robot_view:
        return
    gui.settings.frame.pack_forget()
    gui.robot_panel.frame.pack(side=tk.TOP, fill=tk.X)
    gui.robot_panel.start_poll()
    gui._robot_view = True
    gui.status_var.set("Robot controls — Back to return to main")


def show_main_settings(gui: Any) -> None:
    if not gui._robot_view:
        return
    gui.robot_panel.stop_poll()
    gui.robot_panel.frame.pack_forget()
    gui.settings.refresh_sequences()
    gui.settings.frame.pack(side=tk.TOP, fill=tk.X)
    gui._robot_view = False
    gui.status_var.set("Main settings")
