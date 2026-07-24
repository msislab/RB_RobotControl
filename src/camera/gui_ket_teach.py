"""Sequence teach UI: pick/create sequences/<name>.yaml; record/delete points."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from loguru import logger

from src.camera.gui_focus import bind_release_focus, release_focus
from src.camera.gui_theme import FONT_LABEL
from src.config.ket_store import (
    delete_point,
    ensure_sequence,
    list_sequences,
    record_point,
)
from src.utils.color import yellow


class SequenceTeachBlock:
    """LabelFrame for teaching points into the selected sequence file."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        get_sequence: Callable[[], str],
        set_sequence: Callable[[str], None],
        peek_pose_for_mode: Callable[[str], Optional[object]],
        need_conn: Callable[[], bool],
        set_status: Callable[[str], None],
        on_points_changed: Optional[Callable[[], None]] = None,
    ) -> None:
        self.get_sequence = get_sequence
        self.set_sequence = set_sequence
        self.peek_pose_for_mode = peek_pose_for_mode
        self.need_conn = need_conn
        self.set_status = set_status
        self.on_points_changed = on_points_changed

        self.frame = ttk.LabelFrame(parent, text="Sequence teach", style="Card.TLabelframe")
        self.frame.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(self.frame, text="Sequence file", style="Muted.TLabel", font=FONT_LABEL).pack(
            anchor=tk.W
        )
        row = ttk.Frame(self.frame, style="Surface.TFrame")
        row.pack(fill=tk.X, pady=(0, 4))
        self.seq_var = tk.StringVar(value=get_sequence() or "ket")
        self.seq_box = ttk.Combobox(row, textvariable=self.seq_var, state="readonly")
        self.seq_box.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.seq_box.bind("<<ComboboxSelected>>", self._on_pick)
        bind_release_focus(self.seq_box)
        self.new_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.new_var, width=10).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(row, text="New", width=4, command=self._on_new).pack(side=tk.LEFT, padx=(4, 0))

        ttk.Label(self.frame, text="Point name", style="Muted.TLabel", font=FONT_LABEL).pack(
            anchor=tk.W
        )
        self.point_name = tk.StringVar()
        ttk.Entry(self.frame, textvariable=self.point_name).pack(fill=tk.X, pady=(0, 4))
        self.point_mode = tk.StringVar(value="tcp")
        kr = ttk.Frame(self.frame, style="Surface.TFrame")
        kr.pack(fill=tk.X, pady=(0, 4))
        for lab, val in (("TCP", "tcp"), ("Joint", "joint")):
            ttk.Radiobutton(kr, text=lab, variable=self.point_mode, value=val).pack(
                side=tk.LEFT, padx=(0, 8)
            )
        ttk.Button(self.frame, text="Record position", command=self._on_record).pack(fill=tk.X)
        ttk.Button(self.frame, text="Delete point", command=self._on_delete).pack(
            fill=tk.X, pady=(4, 0)
        )
        self.refresh()

    def refresh(self) -> None:
        names = list_sequences() or ["ket"]
        self.seq_box["values"] = names
        cur = self.get_sequence() or "ket"
        if cur not in names:
            names = sorted(set(names) | {cur})
            self.seq_box["values"] = names
        self.seq_var.set(cur)
        if self.on_points_changed is not None:
            self.on_points_changed()

    def _on_pick(self, _e=None) -> None:
        self.set_sequence(self.seq_var.get())
        self.refresh()
        release_focus(self.seq_box)

    def _on_new(self) -> None:
        name = self.new_var.get().strip()
        try:
            ensure_sequence(name)
            self.set_sequence(name)
            self.new_var.set("")
            self.refresh()
            release_focus(self.seq_box)
            self.set_status(f"Created sequence {name!r}")
        except Exception as e:
            self.set_status(f"Create failed: {e}")

    def _on_record(self) -> None:
        if not self.need_conn():
            return
        name = self.point_name.get().strip()
        mode = self.point_mode.get()
        pose = self.peek_pose_for_mode(mode)
        if pose is None:
            self.set_status("No live pose to record")
            return
        try:
            seq = self.seq_var.get()
            record_point(name, mode, pose, seq)
            self.refresh()
            self.set_status(f"Recorded {name!r} → {seq}")
            logger.info(yellow(f"Recorded {name} in {seq}"))
        except Exception as e:
            self.set_status(f"Record failed: {e}")

    def _on_delete(self) -> None:
        name = self.point_name.get().strip()
        try:
            seq = self.seq_var.get()
            delete_point(name, seq)
            self.refresh()
            self.set_status(f"Deleted {name!r} from {seq}")
        except Exception as e:
            self.set_status(f"Delete failed: {e}")
