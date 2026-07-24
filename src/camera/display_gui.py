"""Tkinter Start/Stop GUI with live RealSense panels."""

from __future__ import annotations

import threading
import tkinter as tk
from typing import Any, Dict, Optional

import cv2
from loguru import logger
from PIL import Image, ImageTk

from src.application.application import RobotApplication
from src.camera.gui_fps import PaneFps, apply_titles, reset_titles
from src.camera.gui_preview import show_preview_keys
from src.camera.gui_shell import build_main_layout
from src.camera.gui_stereo import preview_keys, start_stereo_worker, stop_stereo_worker
from src.camera.gui_theme import apply_theme, maximize_window
from src.camera.realsense_camera import RealSenseCamera
from src.utils.color import green, red, yellow


class CameraControlGui:
    """Start/Stop + settings (locked while running) + live image panels."""

    def __init__(self, app: RobotApplication, *, defaults: Dict[str, Any]) -> None:
        self.app = app
        self.serial = defaults.get("serial")
        self.camera: Optional[RealSenseCamera] = None
        self._stereo = None
        self._stereo_pane = False
        self._running = False
        self._robot_thread: Optional[threading.Thread] = None
        self._photo: Dict[str, ImageTk.PhotoImage] = {}
        self._fps = int(defaults.get("fps", 30))
        self._pane_fps = PaneFps()
        self.root = tk.Tk()
        self.root.title("RobotControl — RealSense")
        self._style = apply_theme(self.root)
        maximize_window(self.root)
        self.root.protocol("WM_DELETE_WINDOW", self._handle_close)
        (
            self.settings, self.start_btn, self.stop_btn, self.status_var,
            self.panel, self._labels, self._frames, self._fit_sidebar,
        ) = build_main_layout(
            self.root, self._style, defaults, self._on_start, self._on_stop
        )

    def run(self) -> None:
        self.root.mainloop()

    def _show_panels(self, view: str, camera_on: bool, stereo_on: bool) -> None:
        show_preview_keys(
            self.panel, self._frames, self._labels, preview_keys(view, camera_on, stereo_on)
        )

    def _on_start(self) -> None:
        if self._running:
            return
        try:
            cfg = self.settings.values()
        except Exception as e:
            self.status_var.set(f"Bad settings: {e}")
            return
        if cfg.get("stereo_enabled") and not cfg.get("camera_enabled"):
            self.status_var.set("Stereo depth requires Enable RealSense")
            return
        self._fps = int(cfg["fps"])
        self._stereo_pane = False
        self._pane_fps.reset()
        if cfg["camera_enabled"]:
            try:
                cam = RealSenseCamera(
                    view=cfg["view"], fps=self._fps, serial=self.serial,
                    width=cfg["width"], height=cfg["height"],
                    force_ir=bool(cfg.get("stereo_enabled")),
                )
                cam.start()
                self.camera = cam
            except Exception as e:
                logger.error("Camera start failed: {}", e)
                self.status_var.set(f"Camera failed: {e}")
                return
            self._stereo = start_stereo_worker(cam, cfg)
        else:
            self.camera = None
            self._stereo = None
        self._running = True
        self.settings.set_locked(True)
        self.start_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)
        self._show_panels(cfg["view"], cfg["camera_enabled"], False)
        self.status_var.set(f"Running · camera={cfg['camera_enabled']} · view={cfg['view']}")
        logger.info(green(f"Start cfg={cfg}"))
        self._start_cfg = cfg
        self._robot_thread = threading.Thread(target=self._robot_worker, daemon=True)
        self._robot_thread.start()
        if self.camera is not None:
            self._schedule_frame()

    def _robot_worker(self) -> None:
        try:
            self.app.setup_with_settings(getattr(self, "_start_cfg", {}))
            self.app.execute_motion_sequence()
        except Exception as e:
            logger.error("Robot worker error: {}", e)
            self.root.after(0, lambda: self.status_var.set(f"Robot error: {e}"))

    def _on_stop(self) -> None:
        if not self._running:
            return
        self._running = False
        self.app.request_stop()
        stop_stereo_worker(self._stereo)
        self._stereo = None
        self._stereo_pane = False
        if self.camera is not None:
            self.camera.stop()
            self.camera = None
        reset_titles(self._frames, self._pane_fps)
        self.settings.set_locked(False)
        self.start_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
        self.status_var.set("Stopped — change settings, then Start")
        logger.info(yellow("Stop requested"))

    def _schedule_frame(self) -> None:
        if not self._running or self.camera is None:
            return
        try:
            frames = self.camera.read()
            self._tick_stereo(frames)
            self._update_images(frames)
        except Exception as e:
            logger.warning("Frame read failed: {}", e)
            self.status_var.set(f"Frame error: {e}")
        self.root.after(max(1, int(1000 / max(1, self._fps))), self._schedule_frame)

    def _tick_stereo(self, frames: Dict) -> None:
        w = self._stereo
        if w is None:
            return
        if w.error and not self._stereo_pane:
            self.status_var.set(f"Stereo unavailable: {w.error}")
            return
        if w.ready and not self._stereo_pane:
            self._stereo_pane = True
            cfg = getattr(self, "_start_cfg", {})
            self._show_panels(cfg.get("view", "rgb"), True, True)
            self.status_var.set("Running · stereo depth ready")
        if w.ready and "ir1" in frames and "ir2" in frames:
            w.submit(frames["ir1"], frames["ir2"])
            heat = w.latest_heatmap()
            if heat is not None:
                frames["stereo_depth"] = heat

    def _fit_bgr(self, bgr, key: str):
        fr = self._frames.get(key)
        if fr is None:
            return bgr
        fr.update_idletasks()
        tw, th = max(120, fr.winfo_width() - 20), max(90, fr.winfo_height() - 36)
        h, w = bgr.shape[:2]
        if w < 1 or h < 1:
            return bgr
        scale = min(tw / float(w), th / float(h))
        nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
        if nw == w and nh == h:
            return bgr
        return cv2.resize(bgr, (nw, nh), interpolation=cv2.INTER_AREA)

    def _update_images(self, frames: Dict) -> None:
        self.panel.update_idletasks()
        shown: Dict[str, object] = {}
        for key, bgr in frames.items():
            if key not in self._labels:
                continue
            bgr = self._fit_bgr(bgr, key)
            photo = ImageTk.PhotoImage(
                image=Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
            )
            self._photo[key] = photo
            self._labels[key].configure(image=photo, text="")
            shown[key] = bgr
        apply_titles(self._frames, self._pane_fps, shown)

    def _handle_close(self) -> None:
        self._running = False
        self.app.request_stop()
        stop_stereo_worker(self._stereo)
        self._stereo = None
        if self.camera is not None:
            self.camera.stop()
            self.camera = None
        try:
            self.app.shutdown()
        except Exception as e:
            logger.error("Shutdown error: {}", e)
        logger.info(red("GUI closed"))
        self.root.destroy()
