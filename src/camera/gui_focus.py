"""Focus helpers so Combobox/radio selection does not eat the next click."""

from __future__ import annotations

import tkinter as tk


def release_focus(widget: tk.Misc) -> None:
    """Drop Combobox/control focus so the next click activates immediately."""
    try:
        if widget.winfo_class() == "TCombobox":
            widget.selection_clear()
            try:
                widget.tk.call("ttk::combobox::Unpost", widget)
            except tk.TclError:
                pass
    except tk.TclError:
        pass

    def _to_root() -> None:
        try:
            widget.winfo_toplevel().focus_set()
        except tk.TclError:
            pass

    try:
        widget.after_idle(_to_root)
    except tk.TclError:
        _to_root()


def bind_release_focus(widget: tk.Misc, *sequences: str) -> None:
    """On sequence(s), release focus after the widget finishes its handlers."""
    seqs = sequences or ("<<ComboboxSelected>>",)

    def _on(_event=None) -> None:
        release_focus(widget)

    for seq in seqs:
        widget.bind(seq, _on, add="+")
