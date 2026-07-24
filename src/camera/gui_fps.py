"""Per-camera FPS meters shown on preview pane titles."""

from __future__ import annotations

import time
from typing import Any, Dict, Mapping, Optional

from src.camera.device_fps import DeviceFpsStore


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
    """One meter per stream key; titles as NAME — m / cam x (cfg t)."""

    def __init__(self) -> None:
        self._meters: Dict[str, FpsMeter] = {}
        self.titles: Dict[str, str] = {}
        self.device_fps: Optional[DeviceFpsStore] = None

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
        if fr is None:
            return
        cam = None if self.device_fps is None else self.device_fps.get(key)
        cam_s = "—" if cam is None else str(int(round(cam)))
        fr.configure(
            text=f"{base} — {meter.measured} / cam {cam_s} (cfg {int(target)})"
        )

    def paint_titles(
        self,
        frames: Dict[str, Any],
        frame_map: Dict[str, Any],
        target: int,
    ) -> None:
        for key in frame_map:
            self.tick_key(key, frames, target)
