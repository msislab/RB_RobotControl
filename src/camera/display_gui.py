"""Tkinter Start/Stop GUI with live RealSense + Omron panels."""

from __future__ import annotations

import tkinter as tk
from typing import Any, Dict, Optional

from loguru import logger

from src.application.application import RobotApplication
from src.camera.gui_camera import apply_live_exposure
from src.camera.gui_fps import CameraFpsBoard
from src.camera.gui_pose import format_run_status, peek_pose
from src.camera.gui_connect import begin_connect, schedule_launch_connect
from src.camera.gui_robot_nav import home_pose, show_main_settings, show_robot_controls
from src.camera.gui_robot_panel import RobotControlPanel
from src.camera.gui_run import begin_start
from src.camera.gui_stop import (
    halt_run, halt_stereo, on_immediate_stop, on_stop, stop_preview_workers,
)
from src.camera.gui_shell import build_main_layout
from src.camera.gui_start import validate_start
from src.camera.gui_theme import apply_theme, maximize_window
from src.camera.omron_camera import OmronCameras, shutdown_omron_devices
from src.camera.realsense_camera import RealSenseCamera
from src.utils.color import red


class CameraControlGui:
    """Start/Stop + settings + shared preview grid for RealSense and Omron."""

    def __init__(self, app: RobotApplication, *, defaults: Dict[str, Any]) -> None:
        self.app = app
        self.defaults = defaults
        self.serial = defaults.get("serial")
        self.camera: Optional[RealSenseCamera] = None
        self.omron: Optional[OmronCameras] = None
        self._running = self._starting = False
        self._connecting = False
        self._robot_thread = None
        self._photo: Dict[str, Any] = {}
        self._fps = int(defaults.get("fps", 30))
        self._fps_board = CameraFpsBoard()
        self._rs_on = False
        self._omron_n = 0
        self._tcp = self._joints = None
        self._live_job: Optional[str] = None
        self._robot_view = False
        self._stereo = None
        self._stereo_pane = False
        self._stopping = False
        self._stop_phase = None
        self._stop_watch_started = False
        self._capture_pool = None
        self._pane_workers = None
        self._frame_hub = None
        self._hide_preview = bool(defaults.get("hide_preview", False))
        self.root = tk.Tk()
        self.root.title("RobotControl — cameras")
        self._style = apply_theme(self.root)
        maximize_window(self.root)
        self.root.protocol("WM_DELETE_WINDOW", self._handle_close)
        (
            self.settings, self._scroll_inner, self.start_btn, self.stop_btn,
            self.immediate_btn, self.status_var, self.panel, self._labels,
            self._frames, self._pane_titles, self._fit_sidebar,
        ) = build_main_layout(
            self.root, self._style, defaults, self._on_start,
            lambda: on_stop(self),
            on_immediate_stop=lambda: on_immediate_stop(self),
            on_live_change=self._schedule_live_apply,
            on_hide_preview=self._on_hide_preview,
            on_open_robot=lambda: show_robot_controls(self),
        )
        self.robot_panel = RobotControlPanel(
            self._scroll_inner,
            app=self.app,
            get_home=lambda: home_pose(self),
            get_sequence=lambda: self.settings.sequence_var.get().strip() or "ket",
            set_sequence=self.settings.set_sequence,
            on_back=lambda: show_main_settings(self),
            set_status=self.status_var.set,
            on_connect=lambda: begin_connect(self),
            is_connecting=lambda: bool(self._connecting),
        )
        self._fps_board.note_titles(self._pane_titles)
        self.root.after(200, self._schedule_pose)
        self.root.after(300, lambda: schedule_launch_connect(self))

    def run(self) -> None:
        self.root.mainloop()

    def _schedule_pose(self) -> None:
        self._tcp, self._joints = peek_pose(self.app)
        # Don't overwrite Stopping… status while a stop watch is in progress.
        if not self._robot_view and not getattr(self, "_stop_phase", None):
            if self._running or (getattr(self.app, "_setup_done", False) and not self._starting):
                text = format_run_status(
                    rs_on=self._rs_on,
                    omron_n=self._omron_n,
                    tcp=self._tcp,
                    joints=self._joints,
                )
                if not self._running:
                    text = text.replace("Running", "Idle", 1)
                if self.status_var.get() != text:
                    self.status_var.set(text)
        self.root.after(500, self._schedule_pose)

    def _schedule_live_apply(self) -> None:
        if not self._running:
            return
        if self._live_job is not None:
            try:
                self.root.after_cancel(self._live_job)
            except tk.TclError:
                pass
        self._live_job = self.root.after(150, self._apply_live_exposure)

    def _apply_live_exposure(self) -> None:
        self._live_job = None
        if self._running:
            try:
                apply_live_exposure(self.settings.values(), self.camera, self.omron)
            except Exception:
                pass

    def _on_hide_preview(self, hide: bool) -> None:
        self._hide_preview = bool(hide)
        if not hide:
            return
        for key, lbl in self._labels.items():
            lbl.configure(image="", text="—")
            self._photo.pop(key, None)
        pool = getattr(self, "_pane_workers", None)
        if pool is not None:
            pool._blanked.clear()

    def _on_start(self) -> None:
        if self._running or self._starting:
            return
        try:
            cfg = self.settings.values()
        except Exception as e:
            self.status_var.set(f"Bad settings: {e}")
            return
        err = validate_start(cfg)
        if err:
            self.status_var.set(err)
            return
        begin_start(self, cfg)

    def _robot_worker(self) -> None:
        try:
            cfg = getattr(self, "_start_cfg", {}) or {}
            logger.info(
                "Robot worker begin routine={!r} merge={}",
                cfg.get("robot_routine"), cfg.get("robot_sequence_merge"),
            )
            self.app.clear_stop_flags()
            self.app.setup_with_settings(cfg)
            from src.application.routines import run_routine
            run_routine(
                self.app,
                cfg.get("robot_routine", "zigzag"),
                cfg.get("robot_sequence", "ket"),
                loop=bool(cfg.get("robot_sequence_loop", False)),
                merge=bool(cfg.get("robot_sequence_merge", False)),
            )
            logger.info("Robot worker: routine finished")
        except Exception as e:
            logger.error("Robot worker error: {}", e)
            self.root.after(0, lambda err=e: self.status_var.set(f"Robot error: {err}"))

    def _stop_cameras(self) -> None:
        stop_preview_workers(self)
        halt_stereo(self)
        if self.camera is not None:
            self.camera.stop()
            self.camera = None
        if self.omron is not None:
            self.omron.stop()
            self.omron = None

    def _halt_run(self) -> None:
        halt_run(self)

    def _handle_close(self) -> None:
        halt_run(self)
        for label, fn in (("Omron", shutdown_omron_devices), ("Robot", self.app.shutdown)):
            try:
                fn()
            except Exception as e:
                logger.error("{} shutdown error: {}", label, e)
        logger.info(red("GUI closed"))
        self.root.destroy()
