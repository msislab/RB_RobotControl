"""Stereo feeder thread: IR submit + heatmap publish (off RealSense loop)."""

from __future__ import annotations

import threading
from typing import Any, Callable, Optional

from loguru import logger

from src.camera.frame_hub import FrameHub


class StereoFeed:
    """Owns one thread; never runs on the RealSense capture loop."""

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
        ir_gen = 0
        while not self._stop.is_set():
            w = self.worker
            if w is None or w.error:
                self._stop.wait(0.05)
                continue
            if w.ready and not self._shown:
                self._shown = True
                if self._on_ready is not None:
                    self._on_ready()
            ir1, ir_gen = self.hub.wait_new("ir1", ir_gen, timeout=0.05)
            if ir1 is not None and w.ready:
                ir2, _ = self.hub.get("ir2")
                if ir2 is not None:
                    w.submit(ir1, ir2)
            heat = w.consume_heatmap() if hasattr(w, "consume_heatmap") else None
            if heat is not None:
                self.hub.publish("stereo_depth", heat)
