"""Preview grid layout helpers for multi-camera Tk panels."""

from __future__ import annotations

import math
import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, List, Sequence

import cv2
from PIL import Image, ImageTk


def fit_bgr(bgr, frames: Dict[str, ttk.LabelFrame], key: str):
    """Fit into pane; never upscale past native preview (saves Tk work)."""
    fr = frames.get(key)
    if fr is None:
        return bgr
    fr.update_idletasks()
    tw, th = max(120, fr.winfo_width() - 20), max(90, fr.winfo_height() - 36)
    h, w = bgr.shape[:2]
    if w < 1 or h < 1:
        return bgr
    scale = min(tw / float(w), th / float(h), 1.0)
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    if nw == w and nh == h:
        return bgr
    return cv2.resize(bgr, (nw, nh), interpolation=cv2.INTER_AREA)


def collect_frames(camera: Any, omron: Any) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if camera is not None:
        out.update(camera.read() or {})
    if omron is not None:
        out.update(omron.read_all() or {})
    return out


def update_images(
    panel: ttk.Frame,
    frames: Dict[str, ttk.LabelFrame],
    labels: Dict[str, tk.Label],
    photo_store: Dict[str, Any],
    frame_map: Dict[str, Any],
) -> None:
    panel.update_idletasks()
    for key, bgr in frame_map.items():
        update_one_image(labels, photo_store, key, fit_bgr(bgr, frames, key))


def update_one_image(
    labels: Dict[str, tk.Label],
    photo_store: Dict[str, Any],
    key: str,
    bgr: Any,
) -> None:
    if key not in labels:
        return
    photo = ImageTk.PhotoImage(
        image=Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
    )
    photo_store[key] = photo
    labels[key].configure(image=photo, text="")


def setup_start_preview(
    panel: ttk.Frame,
    frames: Dict[str, ttk.LabelFrame],
    labels: Dict[str, tk.Label],
    *,
    view: str,
    camera_on: bool,
    omron_ids: Sequence[str],
    titles: Dict[str, str],
    add_pane,
    stereo_on: bool = False,
) -> None:
    """Create Omron panes and show active RealSense + Omron keys."""
    for cid in omron_ids:
        add_pane(panel, labels, frames, cid, cid.upper(), titles)
    show_keys(
        panel,
        frames,
        labels,
        rs_keys(view, camera_on, stereo_on) + list(omron_ids),
    )


def show_keys(
    panel: ttk.Frame,
    frames: Dict[str, ttk.LabelFrame],
    labels: Dict[str, tk.Label],
    keys: Sequence[str],
) -> None:
    """Show equal-sized cells for keys; hide the rest."""
    for fr in frames.values():
        fr.grid_forget()
        fr.pack_forget()
    n = len(keys)
    cols = 1 if n <= 1 else 2 if n <= 4 else math.ceil(math.sqrt(n))
    rows = 1 if n == 0 else math.ceil(n / cols)
    for r in range(max(rows, 2)):
        if r < rows:
            panel.rowconfigure(r, weight=1, uniform="preview_r")
        else:
            panel.rowconfigure(r, weight=0, minsize=0, uniform="preview_r_x")
    for c in range(max(cols, 2)):
        if c < cols:
            panel.columnconfigure(c, weight=1, uniform="preview_c")
        else:
            panel.columnconfigure(c, weight=0, minsize=0, uniform="preview_c_x")
    for i, key in enumerate(keys):
        fr = frames.get(key)
        if fr is None:
            continue
        fr.grid(row=i // cols, column=i % cols, sticky="nsew", padx=6, pady=4)
    active = set(keys)
    for key in frames:
        if key not in active:
            labels[key].configure(image="", text="—")


def rs_keys(view: str, camera_on: bool, stereo_on: bool = False) -> List[str]:
    if not camera_on:
        return []
    keys = ["color"]
    if view in ("rgb_depth", "rgb_depth_ir"):
        keys.append("depth")
    if view == "rgb_depth_ir":
        keys.extend(["ir1", "ir2"])
    if stereo_on:
        keys.append("stereo_depth")
    return keys
