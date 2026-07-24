"""Per-camera FPS meters shown on preview pane titles."""

from __future__ import annotations

import time
from typing import Any, Dict, Mapping


class FpsMeter:
    """Count arrivals in a 1s window (per stream)."""

    def __init__(self) -> None:
        self._t0 = time.monotonic()
        self._n = 0
        self.measured = 0

    def reset(self) -> None:
        self._t0 = time.monotonic()
        self._n = 0
        self.measured = 0

    def tick(self) -> None:
        self._n += 1
        now = time.monotonic()
        dt = now - self._t0
        if dt >= 1.0:
            self.measured = int(round(self._n / dt))
            self._t0 = now
            self._n = 0


class CameraFpsBoard:
    """One meter per stream key; updates LabelFrame titles as NAME — m/t."""

    def __init__(self) -> None:
        self._meters: Dict[str, FpsMeter] = {}
        self.titles: Dict[str, str] = {}

    def reset(self) -> None:
        self._meters.clear()

    def note_titles(self, titles: Mapping[str, str]) -> None:
        self.titles.update(titles)

    def tick_key(self, key: str, frames: Dict[str, Any], target: int) -> None:
        """Advance only this pane's meter (call when that pane actually updates)."""
        meter = self._meters.setdefault(key, FpsMeter())
        meter.tick()
        base = self.titles.get(key, key)
        fr = frames.get(key)
        if fr is not None:
            fr.configure(text=f"{base} — {meter.measured}/{int(target)}")

    def paint_titles(
        self,
        frames: Dict[str, Any],
        frame_map: Dict[str, Any],
        target: int,
    ) -> None:
        for key in frame_map:
            self.tick_key(key, frames, target)
