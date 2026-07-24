"""Saved sequence points list: Go to point / Fill into Move."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, List, Optional, Sequence

import numpy as np
from loguru import logger

from src.camera.gui_theme import FONT_LABEL, style_tk_listbox
from src.config.ket_store import load_ket
from src.utils.color import green, yellow


class SavedPointsBlock:
    """List taught points for the active sequence; move or fill Manual."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        app: Any,
        get_sequence: Callable[[], str],
        need_conn: Callable[[], bool],
        set_status: Callable[[str], None],
        fill_manual: Callable[[str, Sequence[float]], None],
        ui_after: Callable[..., Any],
    ) -> None:
        self.app = app
        self.get_sequence = get_sequence
        self.need_conn = need_conn
        self.set_status = set_status
        self.fill_manual = fill_manual
        self.ui_after = ui_after
        self._names: List[str] = []
        self._moving = False

        self.frame = ttk.LabelFrame(parent, text="Saved points", style="Card.TLabelframe")
        self.frame.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(
            self.frame,
            text="Select a point, then Go to or Fill into Move",
            style="Muted.TLabel",
            font=FONT_LABEL,
        ).pack(anchor=tk.W)
        self.listbox = tk.Listbox(self.frame, height=6, exportselection=False)
        style_tk_listbox(self.listbox)
        self.listbox.pack(fill=tk.X, pady=(4, 4))
        row = ttk.Frame(self.frame, style="Surface.TFrame")
        row.pack(fill=tk.X)
        self.go_btn = ttk.Button(row, text="Go to point", command=self._on_go)
        self.go_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(row, text="Fill into Move", command=self._on_fill).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0)
        )
        self.refresh()

    def refresh(self) -> None:
        seq_name = self.get_sequence() or "ket"
        try:
            data = load_ket(seq_name)
        except Exception as e:
            self.listbox.delete(0, tk.END)
            self._names = []
            self.set_status(f"Load points failed: {e}")
            return
        sel = self.listbox.curselection()
        keep = self._names[sel[0]] if sel else None
        self.listbox.delete(0, tk.END)
        self._names = []
        points = data["points"]
        for name in data["sequence"]:
            pt = points.get(name) or {}
            mode = str(pt.get("mode", "tcp")).lower()
            self.listbox.insert(tk.END, f"{name} ({mode})")
            self._names.append(name)
        if keep and keep in self._names:
            self.listbox.selection_set(self._names.index(keep))

    def _selected(self) -> Optional[tuple]:
        sel = self.listbox.curselection()
        if not sel:
            self.set_status("Select a saved point first")
            return None
        name = self._names[sel[0]]
        data = load_ket(self.get_sequence() or "ket")
        pt = data["points"].get(name)
        if not pt:
            self.set_status(f"Missing point data for {name!r}")
            return None
        mode = str(pt.get("mode", "tcp")).lower()
        pose = [float(v) for v in (pt.get("pose") or [])]
        if len(pose) != 6:
            self.set_status(f"Bad pose for {name!r}")
            return None
        return name, mode, pose

    def _on_fill(self) -> None:
        item = self._selected()
        if item is None:
            return
        name, mode, pose = item
        self.fill_manual(mode, pose)
        self.set_status(f"Filled Move from {name!r} ({mode})")

    def _on_go(self) -> None:
        if self._moving:
            return
        if not self.need_conn():
            return
        item = self._selected()
        if item is None:
            return
        name, mode, pose = item
        self._moving = True
        self.go_btn.configure(state=tk.DISABLED, text="Moving…")
        self.set_status(f"Going to {name!r}…")
        threading.Thread(
            target=self._go_worker, args=(name, mode, pose), daemon=True
        ).start()

    def _go_worker(self, name: str, mode: str, pose: List[float]) -> None:
        try:
            arr = np.array(pose, dtype=float)
            if mode == "joint":
                self.app.controller.move_j(arr)
            else:
                self.app.controller.move_to_point(arr, speed=100, acc=500)
            logger.info(green(f"Go to {name!r} ({mode}) done"))
            self.ui_after(0, lambda: self._go_done(f"Arrived at {name!r}"))
        except Exception as e:
            logger.warning(yellow(f"Go to {name!r} failed: {e}"))
            self.ui_after(0, lambda: self._go_done(f"Go to failed: {e}"))

    def _go_done(self, msg: str) -> None:
        self._moving = False
        self.go_btn.configure(state=tk.NORMAL, text="Go to point")
        self.set_status(msg)
