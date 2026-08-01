"""Per-camera FPS meters shown on preview pane titles."""

from __future__ import annotations

import time
from typing import Any, Dict, Mapping, Optional

from src.camera.device_fps import DeviceMetaStore


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
    """One meter per stream; titles NAME — m / cam x (cfg t) + WxH line."""

    def __init__(self) -> None:
        self._meters: Dict[str, FpsMeter] = {}
        self.titles: Dict[str, str] = {}
        self.device_meta: Optional[DeviceMetaStore] = None

    @property
    def device_fps(self) -> Optional[DeviceMetaStore]:
        return self.device_meta

    @device_fps.setter
    def device_fps(self, store: Optional[DeviceMetaStore]) -> None:
        self.device_meta = store

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
        meta = self.device_meta
        cam = None if meta is None else meta.get_fps(key)
        cam_s = "—" if cam is None else str(int(round(cam)))
        size = None if meta is None else meta.get_size(key)
        size_s = "—" if size is None else f"{size[0]}×{size[1]}"
        fr.configure(
            text=(
                f"{base} — {meter.measured} / cam {cam_s} (cfg {int(target)})\n"
                f"{size_s}"
            )
        )

    def paint_titles(
        self,
        frames: Dict[str, Any],
        frame_map: Dict[str, Any],
        target: int,
    ) -> None:
        for key in frame_map:
            self.tick_key(key, frames, target)
