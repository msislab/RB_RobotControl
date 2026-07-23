"""Tkinter Start/Stop GUI with live RealSense panels."""

from __future__ import annotations

import threading
import tkinter as tk
from typing import Any, Dict, Optional

import cv2
from loguru import logger
from PIL import Image, ImageTk

from src.application.application import RobotApplication
from src.camera.gui_shell import build_main_layout
from src.camera.gui_theme import apply_theme, maximize_window
from src.camera.realsense_camera import RealSenseCamera
from src.utils.color import green, red, yellow


class CameraControlGui:
    """Start/Stop + settings (locked while running) + live image panels."""

    def __init__(self, app: RobotApplication, *, defaults: Dict[str, Any]) -> None:
        self.app = app
        self.serial = defaults.get("serial")
        self.camera: Optional[RealSenseCamera] = None
        self._running = False
        self._robot_thread: Optional[threading.Thread] = None
        self._photo: Dict[str, ImageTk.PhotoImage] = {}
        self._fps = int(defaults.get("fps", 30))

        self.root = tk.Tk()
        self.root.title("RobotControl — RealSense")
        self._style = apply_theme(self.root)
        maximize_window(self.root)
        self.root.protocol("WM_DELETE_WINDOW", self._handle_close)

        (
            self.settings,
            self.start_btn,
            self.stop_btn,
            self.status_var,
            self.panel,
            self._labels,
            self._frames,
            self._fit_sidebar,
        ) = build_main_layout(
            self.root, self._style, defaults, self._on_start, self._on_stop
        )

    def run(self) -> None:
        self.root.mainloop()

    def _show_panels_for_view(self, view: str, camera_on: bool) -> None:
        keys = []
        if camera_on:
            keys = ["color"]
            if view in ("rgb_depth", "rgb_depth_ir"):
                keys.append("depth")
            if view == "rgb_depth_ir":
                keys.extend(["ir1", "ir2"])
        # Equal cells via uniform; layout by count (1 / 1x2 / 2x2).
        for fr in self._frames.values():
            fr.grid_forget()
            fr.pack_forget()
        n = len(keys)
        cols = 1 if n <= 1 else 2
        rows = 1 if n <= 2 else 2
        for r in range(2):
            if r < rows:
                self.panel.rowconfigure(r, weight=1, uniform="preview_r")
            else:
                self.panel.rowconfigure(r, weight=0, minsize=0, uniform="preview_r_x")
        for c in range(2):
            if c < cols:
                self.panel.columnconfigure(c, weight=1, uniform="preview_c")
            else:
                self.panel.columnconfigure(c, weight=0, minsize=0, uniform="preview_c_x")
        for i, key in enumerate(keys):
            fr = self._frames[key]
            fr.grid(
                row=i // cols, column=i % cols, sticky="nsew", padx=6, pady=4
            )
        for key in self._frames:
            if key not in keys:
                self._labels[key].configure(image="", text="—")

    def _on_start(self) -> None:
        if self._running:
            return
        try:
            cfg = self.settings.values()
        except Exception as e:
            self.status_var.set(f"Bad settings: {e}")
            return

        self._fps = int(cfg["fps"])
        if cfg["camera_enabled"]:
            try:
                cam = RealSenseCamera(
                    view=cfg["view"], fps=self._fps, serial=self.serial,
                    width=cfg["width"], height=cfg["height"],
                )
                cam.start()
                self.camera = cam
            except Exception as e:
                logger.error("Camera start failed: {}", e)
                self.status_var.set(f"Camera failed: {e}")
                return
        else:
            self.camera = None

        self._running = True
        self.settings.set_locked(True)
        self.start_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)
        self._show_panels_for_view(cfg["view"], cfg["camera_enabled"])
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
        if self.camera is not None:
            self.camera.stop()
            self.camera = None
        self.settings.set_locked(False)
        self.start_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
        self.status_var.set("Stopped — change settings, then Start")
        logger.info(yellow("Stop requested"))

    def _schedule_frame(self) -> None:
        if not self._running or self.camera is None:
            return
        try:
            self._update_images(self.camera.read())
        except Exception as e:
            logger.warning("Frame read failed: {}", e)
            self.status_var.set(f"Frame error: {e}")
        self.root.after(max(1, int(1000 / max(1, self._fps))), self._schedule_frame)

    def _fit_bgr(self, bgr, key: str):
        """Resize frame to fill its preview cell while keeping aspect ratio."""
        fr = self._frames.get(key)
        if fr is None:
            return bgr
        fr.update_idletasks()
        tw = max(120, fr.winfo_width() - 20)
        th = max(90, fr.winfo_height() - 36)
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
        for key, bgr in frames.items():
            if key not in self._labels:
                continue
            bgr = self._fit_bgr(bgr, key)
            photo = ImageTk.PhotoImage(
                image=Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
            )
            self._photo[key] = photo
            self._labels[key].configure(image=photo, text="")

    def _handle_close(self) -> None:
        self._running = False
        self.app.request_stop()
        if self.camera is not None:
            self.camera.stop()
            self.camera = None
        try:
            self.app.shutdown()
        except Exception as e:
            logger.error("Shutdown error: {}", e)
        logger.info(red("GUI closed"))
        self.root.destroy()
