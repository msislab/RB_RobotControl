"""Thread-safe live device FPS values for preview pane titles."""

from __future__ import annotations

import threading
from typing import Dict, Optional


class DeviceFpsStore:
    """Latest device-reported actual FPS per stream key (None = unavailable)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._fps: Dict[str, Optional[float]] = {}

    def clear(self) -> None:
        with self._lock:
            self._fps.clear()

    def set(self, key: str, fps: Optional[float]) -> None:
        with self._lock:
            self._fps[key] = fps

    def get(self, key: str) -> Optional[float]:
        with self._lock:
            return self._fps.get(key)
