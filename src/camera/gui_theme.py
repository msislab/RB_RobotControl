"""Tk theme + window helpers for the control GUI."""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import ttk

BG = "#14181e"
SURFACE = "#1e252e"
SURFACE_2 = "#283039"
BORDER = "#3a4654"
TEXT = "#e7edf4"
MUTED = "#8b97a8"
ACCENT = "#2a9d8f"
START = "#2f9e6b"
STOP = "#c45c4a"
SIDEBAR_WIDTH = 620

# Logical point sizes (Tk scales with display DPI).
MIN_FONT = 15
FONT_FAMILY = "DejaVu Sans"
FONT_UI = (FONT_FAMILY, MIN_FONT)
FONT_UI_BOLD = (FONT_FAMILY, MIN_FONT, "bold")
FONT_LABEL = (FONT_FAMILY, MIN_FONT)
FONT_TITLE = (FONT_FAMILY, 20, "bold")


def detect_tk_scaling(root: tk.Tk) -> float:
    """
    Tk scaling = pixels per point (72pt = 1 inch).

    Prefer GDK_SCALE / QT_SCALE_FACTOR when set (common on Linux HiDPI),
    else derive from screen DPI. Clamp to 1.0–2.0.
    """
    for key in ("GDK_SCALE", "QT_SCALE_FACTOR"):
        raw = os.environ.get(key)
        if not raw:
            continue
        try:
            return max(1.0, min(2.0, round(float(raw), 2)))
        except ValueError:
            pass
    try:
        dpi = float(root.winfo_fpixels("1i"))
    except tk.TclError:
        dpi = 96.0
    if dpi < 1.0:
        dpi = 96.0
    return max(1.0, min(2.0, round(dpi / 72.0, 2)))


def maximize_window(root: tk.Tk) -> None:
    """Maximize with window chrome (not fullscreen)."""
    root.update_idletasks()
    for apply in (
        lambda: root.state("zoomed"),
        lambda: root.attributes("-zoomed", True),
    ):
        try:
            apply()
            return
        except tk.TclError:
            continue
    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{w}x{h}+0+0")


def apply_density(style: ttk.Style, density: float = 1.0) -> None:
    """Apply fonts (≥15pt) and compact padding. density only affects padding."""
    d = max(0.85, min(1.15, float(density)))
    pad_card = max(6, int(round(8 * d)))
    pad_entry = max(2, int(round(3 * d)))
    pad_btn = (max(14, int(round(16 * d))), max(8, int(round(10 * d))))

    style.configure(".", font=FONT_UI)
    style.configure("TLabel", font=FONT_UI)
    style.configure("Surface.TLabel", font=FONT_UI)
    style.configure("Muted.TLabel", font=FONT_LABEL)
    style.configure("Title.TLabel", font=FONT_TITLE)
    style.configure("Status.TLabel", font=FONT_UI)
    style.configure("TCheckbutton", font=FONT_UI)
    style.configure("TRadiobutton", font=FONT_UI)
    style.configure("TCombobox", font=FONT_UI)
    style.configure("Card.TLabelframe", padding=pad_card)
    style.configure("Card.TLabelframe.Label", font=FONT_UI_BOLD)
    style.configure("Preview.TLabelframe.Label", font=FONT_LABEL)
    style.configure("TEntry", padding=pad_entry, font=FONT_UI)
    style.configure("TButton", font=FONT_UI_BOLD, padding=pad_btn)
    style.configure("Start.TButton", font=FONT_UI_BOLD, padding=pad_btn)
    style.configure("Stop.TButton", font=FONT_UI_BOLD, padding=pad_btn)


def style_tk_listbox(lb: tk.Listbox) -> None:
    """Match dark theme + UI font on a raw Tk Listbox."""
    lb.configure(
        bg=SURFACE_2,
        fg=TEXT,
        selectbackground=ACCENT,
        selectforeground="#ffffff",
        highlightthickness=1,
        highlightbackground=BORDER,
        highlightcolor=ACCENT,
        borderwidth=0,
        relief=tk.FLAT,
        font=FONT_UI,
        activestyle="dotbox",
    )


def apply_theme(root: tk.Tk) -> ttk.Style:
    """Apply dark control-panel ttk styles; set root background + HiDPI scaling."""
    root.configure(bg=BG)
    try:
        root.tk.call("tk", "scaling", detect_tk_scaling(root))
    except tk.TclError:
        pass
    root.option_add("*Font", FONT_UI)
    root.option_add("*TCombobox*Listbox.font", FONT_UI)
    root.option_add("*Listbox.font", FONT_UI)

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(".", background=BG, foreground=TEXT, borderwidth=0, font=FONT_UI)
    style.configure("TFrame", background=BG)
    style.configure("Surface.TFrame", background=SURFACE)
    style.configure("TLabel", background=BG, foreground=TEXT, font=FONT_UI)
    style.configure("Surface.TLabel", background=SURFACE, foreground=TEXT, font=FONT_UI)
    style.configure("Muted.TLabel", background=SURFACE, foreground=MUTED, font=FONT_LABEL)
    style.configure("Title.TLabel", background=BG, foreground=TEXT, font=FONT_TITLE)
    style.configure("Status.TLabel", background=SURFACE_2, foreground=TEXT, font=FONT_UI)
    style.configure("TCheckbutton", background=SURFACE, foreground=TEXT, font=FONT_UI)
    style.configure("TRadiobutton", background=SURFACE, foreground=TEXT, font=FONT_UI)
    style.map("TRadiobutton", background=[("active", SURFACE_2)])
    style.map("TCheckbutton", background=[("active", SURFACE_2)])
    style.configure(
        "Card.TLabelframe",
        background=SURFACE, foreground=TEXT, bordercolor=BORDER,
        relief="solid", borderwidth=1, padding=8,
    )
    style.configure(
        "Card.TLabelframe.Label",
        background=SURFACE, foreground=ACCENT, font=FONT_UI_BOLD,
    )
    style.configure(
        "Preview.TLabelframe",
        background=SURFACE_2, foreground=MUTED, bordercolor=BORDER,
        relief="solid", borderwidth=1, padding=6,
    )
    style.configure(
        "Preview.TLabelframe.Label",
        background=SURFACE_2, foreground=MUTED, font=FONT_LABEL,
    )
    style.configure(
        "TEntry",
        fieldbackground=SURFACE_2, foreground=TEXT, insertcolor=TEXT,
        bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
        padding=3, font=FONT_UI,
    )
    style.map("TEntry", bordercolor=[("focus", ACCENT)])
    style.configure(
        "TCombobox",
        fieldbackground=SURFACE_2, foreground=TEXT, background=SURFACE_2,
        bordercolor=BORDER, arrowcolor=TEXT, font=FONT_UI,
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", SURFACE_2)],
        selectbackground=[("readonly", SURFACE_2)],
        selectforeground=[("readonly", TEXT)],
        bordercolor=[("focus", ACCENT)],
    )
    style.configure(
        "Horizontal.TScale",
        background=SURFACE, troughcolor=SURFACE_2, bordercolor=BORDER,
        lightcolor=ACCENT, darkcolor=ACCENT,
    )
    style.configure("TButton", background=SURFACE_2, font=FONT_UI_BOLD, padding=(16, 10))
    style.map("TButton", background=[("active", BORDER), ("disabled", SURFACE)])
    style.configure("Start.TButton", background=START, foreground="#ffffff")
    style.map("Start.TButton", background=[("active", "#268a5c"), ("disabled", "#3a5a4a")])
    style.configure("Stop.TButton", background=STOP, foreground="#ffffff")
    style.map("Stop.TButton", background=[("active", "#a84b3c"), ("disabled", "#5a3a36")])
    apply_density(style, 1.0)
    return style
