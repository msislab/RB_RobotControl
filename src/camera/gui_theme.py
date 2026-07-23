"""Tk theme + window helpers for the control GUI."""

from __future__ import annotations

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
SIDEBAR_WIDTH = 560

# Hard minimums — never go below 15pt for UI text.
MIN_FONT = 15
FONT_UI = ("DejaVu Sans", MIN_FONT)
FONT_UI_BOLD = ("DejaVu Sans", MIN_FONT, "bold")
FONT_LABEL = ("DejaVu Sans", MIN_FONT)
FONT_TITLE = ("DejaVu Sans", 22, "bold")


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
    pad_card = max(4, int(round(6 * d)))
    pad_entry = max(1, int(round(2 * d)))  # slim fields vs large text
    pad_btn = (max(14, int(round(16 * d))), max(6, int(round(8 * d))))

    style.configure(".", font=FONT_UI)
    style.configure("TLabel", font=FONT_UI)
    style.configure("Surface.TLabel", font=FONT_UI)
    style.configure("Muted.TLabel", font=FONT_LABEL)
    style.configure("Title.TLabel", font=FONT_TITLE)
    style.configure("Status.TLabel", font=FONT_UI)
    style.configure("TCheckbutton", font=FONT_UI)
    style.configure("TRadiobutton", font=FONT_UI)
    style.configure("Card.TLabelframe", padding=pad_card)
    style.configure("Card.TLabelframe.Label", font=FONT_UI_BOLD)
    style.configure("Preview.TLabelframe.Label", font=FONT_LABEL)
    style.configure("TEntry", padding=pad_entry, font=FONT_UI)
    style.configure("TButton", font=FONT_UI_BOLD, padding=pad_btn)
    style.configure("Start.TButton", font=FONT_UI_BOLD, padding=pad_btn)
    style.configure("Stop.TButton", font=FONT_UI_BOLD, padding=pad_btn)


def apply_theme(root: tk.Tk) -> ttk.Style:
    """Apply dark control-panel ttk styles; set root background."""
    root.configure(bg=BG)
    # Predictable point sizes (avoid HiDPI under-sizing labels).
    try:
        root.tk.call("tk", "scaling", 1.25)
    except tk.TclError:
        pass
    root.option_add("*Font", FONT_UI)

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
        relief="solid", borderwidth=1, padding=6,
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
        padding=2, font=FONT_UI,
    )
    style.map("TEntry", bordercolor=[("focus", ACCENT)])
    style.configure(
        "Horizontal.TScale",
        background=SURFACE, troughcolor=SURFACE_2, bordercolor=BORDER,
        lightcolor=ACCENT, darkcolor=ACCENT,
    )
    style.configure("TButton", background=SURFACE_2, font=FONT_UI_BOLD, padding=(16, 8))
    style.map("TButton", background=[("active", BORDER), ("disabled", SURFACE)])
    style.configure("Start.TButton", background=START, foreground="#ffffff")
    style.map("Start.TButton", background=[("active", "#268a5c"), ("disabled", "#3a5a4a")])
    style.configure("Stop.TButton", background=STOP, foreground="#ffffff")
    style.map("Stop.TButton", background=[("active", "#a84b3c"), ("disabled", "#5a3a36")])
    apply_density(style, 1.0)
    return style
