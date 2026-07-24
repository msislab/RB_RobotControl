"""Background capture threads: 1× RealSense, 1× per Omron camera."""

from __future__ import annotations

import threading
import time
from typing import Any, List, Optional

from loguru import logger

from src.camera.frame_hub import FrameHub
from src.camera.stereo_feed import StereoFeed


class CapturePool:
    """Own thread per camera device; publishes into ``FrameHub``."""

    def __init__(self, hub: FrameHub) -> None:
        self.hub = hub
        self._stop = threading.Event()
        self._threads: List[threading.Thread] = []
        self._stereo_feed: Optional[StereoFeed] = None

    def start(
        self,
        *,
        camera: Any = None,
        omron: Any = None,
        stereo: Any = None,
        target_fps: int = 30,
        on_stereo_ready=None,
    ) -> None:
        self.stop()
        self._stop.clear()
        period = 1.0 / max(1, int(target_fps))
        if camera is not None:
            self._threads.append(
                threading.Thread(
                    target=self._rs_loop,
                    args=(camera, period),
                    name="capture-realsense",
                    daemon=True,
                )
            )
        if omron is not None:
            for cid in list(omron.camera_ids):
                self._threads.append(
                    threading.Thread(
                        target=self._omron_loop,
                        args=(omron, cid, period),
                        name=f"capture-omron-{cid}",
                        daemon=True,
                    )
                )
        for t in self._threads:
            t.start()
        if stereo is not None:
            self._stereo_feed = StereoFeed(
                self.hub, stereo, on_ready=on_stereo_ready
            )
            self._stereo_feed.start()
        logger.info("CapturePool started ({} camera threads)", len(self._threads))

    def stop(self) -> None:
        self._stop.set()
        if self._stereo_feed is not None:
            self._stereo_feed.stop()
            self._stereo_feed = None
        for t in self._threads:
            t.join(timeout=1.0)
        self._threads = []
        self.hub.clear()

    def _rs_loop(self, camera: Any, period: float) -> None:
        while not self._stop.is_set():
            t0 = time.monotonic()
            try:
                frames = camera.read() or {}
            except Exception as e:
                logger.warning("RealSense capture: {}", e)
                frames = {}
            for key, bgr in frames.items():
                self.hub.publish(key, bgr)
            self._sleep(period, t0)

    def _omron_loop(self, omron: Any, cid: str, period: float) -> None:
        # Don't artificially cap Omron to the RealSense GUI fps sleep when
        # retrieve already paced the camera; use a short floor only.
        omron_period = min(period, 1.0 / 60.0)
        while not self._stop.is_set():
            t0 = time.monotonic()
            try:
                bgr = omron.read_one(cid)
            except Exception as e:
                logger.warning("Omron {} capture: {}", cid, e)
                bgr = None
            if bgr is not None:
                self.hub.publish(cid, bgr)
            self._sleep(omron_period, t0)

    @staticmethod
    def _sleep(period: float, t0: float) -> None:
        dt = period - (time.monotonic() - t0)
        if dt > 0:
            time.sleep(dt)
