"""Robot control sidebar: collision, home/move, sequence teach."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, List, Optional

import numpy as np
from loguru import logger

from src.camera.gui_ket_teach import SequenceTeachBlock
from src.camera.gui_pose import peek_collision, peek_pose, robot_connected
from src.camera.gui_seq_points import SavedPointsBlock
from src.camera.gui_theme import FONT_LABEL
from src.utils.color import green, yellow


class RobotControlPanel:
    """Packed into the same scroll area as SettingsPanel."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        app: Any,
        get_home: Callable[[], List[float]],
        get_sequence: Callable[[], str],
        set_sequence: Callable[[str], None],
        on_back: Callable[[], None],
        set_status: Callable[[str], None],
        on_connect: Callable[[], None],
        is_connecting: Callable[[], bool],
    ) -> None:
        self.app = app
        self.get_home = get_home
        self.on_back = on_back
        self.set_status = set_status
        self.on_connect = on_connect
        self.is_connecting = is_connecting
        self._poll = False
        self.frame = ttk.Frame(parent, style="Surface.TFrame")

        ttk.Button(self.frame, text="← Back to main", command=on_back).pack(
            fill=tk.X, pady=(0, 8)
        )

        st = ttk.LabelFrame(self.frame, text="Robot status", style="Card.TLabelframe")
        st.pack(fill=tk.X, pady=(0, 6))
        self.coll_var = tk.StringVar(value="Status: —")
        ttk.Label(st, textvariable=self.coll_var, style="Status.TLabel").pack(anchor=tk.W)
        self.connect_btn = ttk.Button(
            st, text="Connect to robot", command=self._on_connect_click
        )
        self.connect_btn.pack(fill=tk.X, pady=(6, 0))
        self.resume_btn = ttk.Button(st, text="Resume", command=self._on_resume, state=tk.DISABLED)
        self.resume_btn.pack(fill=tk.X, pady=(6, 0))
        self.sync_connect_btn()

        man = ttk.LabelFrame(self.frame, text="Manual", style="Card.TLabelframe")
        man.pack(fill=tk.X, pady=(0, 6))
        ttk.Button(man, text="Go Home", command=self._on_home).pack(fill=tk.X, pady=(0, 4))

        self.move_mode = tk.StringVar(value="tcp")
        mode_row = ttk.Frame(man, style="Surface.TFrame")
        mode_row.pack(fill=tk.X, pady=(0, 4))
        for lab, val in (("TCP", "tcp"), ("Joint", "joint")):
            ttk.Radiobutton(mode_row, text=lab, variable=self.move_mode, value=val).pack(
                side=tk.LEFT, padx=(0, 8)
            )
        self.move_vars = [tk.StringVar(value="0.0") for _ in range(6)]
        labels = ("x/j0", "y/j1", "z/j2", "rx/j3", "ry/j4", "rz/j5")
        grid = ttk.Frame(man, style="Surface.TFrame")
        grid.pack(fill=tk.X)
        for i, (lab, var) in enumerate(zip(labels, self.move_vars)):
            cell = ttk.Frame(grid, style="Surface.TFrame")
            cell.grid(row=i // 3, column=i % 3, sticky="ew", padx=2, pady=2)
            ttk.Label(cell, text=lab, style="Muted.TLabel", font=FONT_LABEL).pack(anchor=tk.W)
            ttk.Entry(cell, textvariable=var, width=10).pack(fill=tk.X)
        ttk.Button(man, text="Move", command=self._on_move).pack(fill=tk.X, pady=(6, 0))
        ttk.Button(man, text="Fill from current pose", command=self._fill_current).pack(
            fill=tk.X, pady=(4, 0)
        )

        self.teach = SequenceTeachBlock(
            self.frame,
            get_sequence=get_sequence,
            set_sequence=set_sequence,
            peek_pose_for_mode=self._pose_for_mode,
            need_conn=self._need_conn,
            set_status=set_status,
            on_points_changed=lambda: None,
        )
        self.saved = SavedPointsBlock(
            self.frame,
            app=app,
            get_sequence=get_sequence,
            need_conn=self._need_conn,
            set_status=set_status,
            fill_manual=self._fill_manual,
            ui_after=self.frame.after,
        )
        self.teach.on_points_changed = self.saved.refresh

    def start_poll(self) -> None:
        self._poll = True
        self.teach.refresh()
        self.saved.refresh()
        self.sync_connect_btn()
        self._tick_collision()

    def stop_poll(self) -> None:
        self._poll = False

    def sync_connect_btn(self) -> None:
        if robot_connected(self.app):
            self.connect_btn.configure(text="Connected", state=tk.DISABLED)
        elif self.is_connecting():
            self.connect_btn.configure(text="Connecting…", state=tk.DISABLED)
        else:
            self.connect_btn.configure(text="Connect to robot", state=tk.NORMAL)

    def _on_connect_click(self) -> None:
        if robot_connected(self.app) or self.is_connecting():
            return
        self.on_connect()

    def _tick_collision(self) -> None:
        if not self._poll:
            return
        try:
            self.sync_connect_btn()
            if not robot_connected(self.app):
                self.coll_var.set("Status: disconnected")
                self.resume_btn.configure(state=tk.DISABLED)
            else:
                c = peek_collision(self.app)
                self.coll_var.set("Status: Collision" if c else "Status: Normal")
                self.resume_btn.configure(state=tk.NORMAL if c else tk.DISABLED)
        except Exception:
            pass
        self.frame.after(500, self._tick_collision)

    def _need_conn(self) -> bool:
        if robot_connected(self.app):
            return True
        self.set_status("Connect robot first (Connect button or Enable Robot at launch)")
        return False

    def _pose_for_mode(self, mode: str) -> Optional[object]:
        tcp, joints = peek_pose(self.app)
        return joints if mode == "joint" else tcp

    def _on_resume(self) -> None:
        if not self._need_conn():
            return
        try:
            self.app.controller.task_resume(collision=True)
            self.set_status("Collision resume sent")
            logger.info(green("task_resume(collision=True)"))
        except Exception as e:
            self.set_status(f"Resume failed: {e}")
            logger.warning(yellow(f"Resume failed: {e}"))

    def _on_home(self) -> None:
        if not self._need_conn():
            return
        try:
            home = np.array(self.get_home(), dtype=float)
            self.app.controller.move_to_point(home, speed=100, acc=500)
            self.set_status("Go Home sent")
        except Exception as e:
            self.set_status(f"Go Home failed: {e}")

    def _on_move(self) -> None:
        if not self._need_conn():
            return
        try:
            pose = np.array([float(v.get()) for v in self.move_vars], dtype=float)
            if self.move_mode.get() == "joint":
                self.app.controller.move_j(pose)
            else:
                self.app.controller.move_to_point(pose, speed=100, acc=500)
            self.set_status("Move sent")
        except Exception as e:
            self.set_status(f"Move failed: {e}")

    def _fill_manual(self, mode: str, pose: List[float]) -> None:
        self.move_mode.set("joint" if mode == "joint" else "tcp")
        for var, val in zip(self.move_vars, pose):
            var.set(f"{float(val):.2f}")

    def _fill_current(self) -> None:
        tcp, joints = peek_pose(self.app)
        src = joints if self.move_mode.get() == "joint" else tcp
        if src is None:
            self.set_status("No live pose (robot not connected)")
            return
        self._fill_manual(self.move_mode.get(), list(src))
