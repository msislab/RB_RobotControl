"""Thread-safe frame hub backed by SharedMemory double-buffers."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from multiprocessing.shared_memory import SharedMemory
from typing import Dict, Optional, Tuple

import numpy as np

from src.camera.preview_scale import downscale_preview


@dataclass
class _KeyBuf:
    shape: Tuple[int, int, int]
    shm: SharedMemory
    views: Tuple[np.ndarray, np.ndarray]
    read_i: int = 0
    write_i: int = 1
    gen: int = 0


class FrameHub:
    """Publish preview frames into shm slots; consumers get a small numpy copy."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cv = threading.Condition(self._lock)
        self._bufs: Dict[str, _KeyBuf] = {}

    def clear(self) -> None:
        with self._cv:
            for buf in self._bufs.values():
                self._release(buf)
            self._bufs.clear()
            self._cv.notify_all()

    def publish(self, key: str, frame: np.ndarray) -> int:
        if frame is None or getattr(frame, "size", 0) == 0:
            with self._lock:
                buf = self._bufs.get(key)
                return 0 if buf is None else buf.gen
        small = downscale_preview(frame)
        shape = (int(small.shape[0]), int(small.shape[1]), int(small.shape[2]))
        with self._cv:
            buf = self._bufs.get(key)
            if buf is None or buf.shape != shape:
                if buf is not None:
                    self._release(buf)
                buf = self._alloc(shape)
                self._bufs[key] = buf
            np.copyto(buf.views[buf.write_i], small)
            buf.read_i = buf.write_i
            buf.write_i = 1 - buf.write_i
            buf.gen += 1
            self._cv.notify_all()
            return buf.gen

    def get(self, key: str) -> Tuple[Optional[np.ndarray], int]:
        with self._lock:
            buf = self._bufs.get(key)
            if buf is None or buf.gen <= 0:
                return None, 0
            return buf.views[buf.read_i].copy(), buf.gen

    def wait_new(
        self, key: str, after_gen: int, timeout: float = 0.2
    ) -> Tuple[Optional[np.ndarray], int]:
        with self._cv:
            ok = self._cv.wait_for(
                lambda: self._bufs.get(key) is not None
                and self._bufs[key].gen > after_gen,
                timeout=timeout,
            )
            if not ok:
                return None, after_gen
            buf = self._bufs[key]
            return buf.views[buf.read_i].copy(), buf.gen

    def wait_new_gen(self, key: str, after_gen: int, timeout: float = 0.2) -> int:
        """Wait for a new generation without copying pixel data (FPS-only path)."""
        with self._cv:
            ok = self._cv.wait_for(
                lambda: self._bufs.get(key) is not None
                and self._bufs[key].gen > after_gen,
                timeout=timeout,
            )
            if not ok:
                return after_gen
            return self._bufs[key].gen

    @staticmethod
    def _alloc(shape: Tuple[int, int, int]) -> _KeyBuf:
        nbytes = int(np.prod(shape)) * 2  # double buffer
        shm = SharedMemory(create=True, size=nbytes)
        flat = np.ndarray((nbytes,), dtype=np.uint8, buffer=shm.buf)
        n = int(np.prod(shape))
        v0 = flat[:n].reshape(shape)
        v1 = flat[n : 2 * n].reshape(shape)
        return _KeyBuf(shape=shape, shm=shm, views=(v0, v1))

    @staticmethod
    def _release(buf: _KeyBuf) -> None:
        try:
            buf.shm.close()
            buf.shm.unlink()
        except Exception:
            pass
