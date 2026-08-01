"""Thread-safe device stream metadata for preview pane titles."""

from __future__ import annotations

import threading
from typing import Dict, Optional, Tuple

Size = Tuple[int, int]


class DeviceMetaStore:
    """Latest device-reported FPS and capture size per stream key."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._fps: Dict[str, Optional[float]] = {}
        self._size: Dict[str, Optional[Size]] = {}

    def clear(self) -> None:
        with self._lock:
            self._fps.clear()
            self._size.clear()

    def set_fps(self, key: str, fps: Optional[float]) -> None:
        with self._lock:
            self._fps[key] = fps

    def get_fps(self, key: str) -> Optional[float]:
        with self._lock:
            return self._fps.get(key)

    def set_size(self, key: str, size: Optional[Size]) -> None:
        with self._lock:
            self._size[key] = size

    def get_size(self, key: str) -> Optional[Size]:
        with self._lock:
            return self._size.get(key)


# Back-compat alias used by older call sites during rename.
DeviceFpsStore = DeviceMetaStore
