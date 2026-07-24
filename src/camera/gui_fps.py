"""Measured per-pane FPS for preview LabelFrame titles."""

from __future__ import annotations

import time
from typing import Dict, Mapping, MutableMapping, Optional

# key -> display title (without FPS suffix)
PANE_TITLES: Dict[str, str] = {
    "color": "RGB",
    "depth": "Depth",
    "ir1": "IR1",
    "ir2": "IR2",
    "stereo_depth": "Stereo depth",
}


class PaneFps:
    """Exponential FPS from inter-update intervals (per pane key)."""

    def __init__(self, *, alpha: float = 0.25) -> None:
        self._alpha = float(alpha)
        self._last: Dict[str, float] = {}
        self._fps: Dict[str, float] = {}

    def reset(self) -> None:
        self._last.clear()
        self._fps.clear()

    def tick(self, key: str) -> float:
        now = time.perf_counter()
        prev = self._last.get(key)
        self._last[key] = now
        if prev is None:
            return self._fps.get(key, 0.0)
        dt = now - prev
        if dt <= 1e-6:
            return self._fps.get(key, 0.0)
        inst = 1.0 / dt
        prev_fps = self._fps.get(key)
        fps = inst if prev_fps is None else (self._alpha * inst + (1.0 - self._alpha) * prev_fps)
        self._fps[key] = fps
        return fps

    def title_for(self, key: str) -> str:
        base = PANE_TITLES.get(key, key)
        fps = self._fps.get(key)
        if fps is None or fps <= 0:
            return base
        return f"{base}  {fps:.0f} fps"


def apply_titles(
    frames: Mapping[str, object],
    meter: PaneFps,
    updated_keys: Optional[MutableMapping[str, object]] = None,
) -> None:
    """Tick FPS for updated keys and refresh LabelFrame ``text``."""
    keys = updated_keys if updated_keys is not None else frames
    for key in keys:
        fr = frames.get(key)
        if fr is None:
            continue
        meter.tick(key)
        try:
            fr.configure(text=meter.title_for(key))  # type: ignore[attr-defined]
        except Exception:
            pass


def reset_titles(frames: Mapping[str, object], meter: PaneFps) -> None:
    meter.reset()
    for key, fr in frames.items():
        try:
            fr.configure(text=PANE_TITLES.get(key, key))  # type: ignore[attr-defined]
        except Exception:
            pass
