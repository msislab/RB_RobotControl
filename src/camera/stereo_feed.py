"""Stereo feeder thread: heatmap publish only (native IR submitted by capture)."""

from __future__ import annotations

import threading
from typing import Any, Callable, Optional

from loguru import logger

from src.camera.frame_hub import FrameHub


class StereoFeed:
    """Publishes stereo heatmaps into the hub; IR infer is fed elsewhere."""

    def __init__(
        self,
        hub: FrameHub,
        worker: Any,
        *,
        on_ready: Optional[Callable[[], None]] = None,
    ) -> None:
        self.hub = hub
        self.worker = worker
        self._on_ready = on_ready
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._shown = False

    def start(self) -> None:
        self.stop()
        self._stop.clear()
        self._shown = False
        self._thread = threading.Thread(
            target=self._loop, name="stereo-feed", daemon=True
        )
        self._thread.start()
        logger.info("StereoFeed thread started")

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.5)
            self._thread = None

    def _loop(self) -> None:
        while not self._stop.is_set():
            w = self.worker
            if w is None or w.error:
                self._stop.wait(0.05)
                continue
            if w.ready and not self._shown:
                self._shown = True
                if self._on_ready is not None:
                    self._on_ready()
            heat = w.consume_heatmap() if hasattr(w, "consume_heatmap") else None
            if heat is not None:
                self.hub.publish("stereo_depth", heat)
            else:
                self._stop.wait(0.01)
