"""Background capture threads: 1× RealSense, 1× per Omron camera."""

from __future__ import annotations

import threading
import time
from typing import Any, List, Optional, Tuple

from loguru import logger

from src.camera.device_fps import DeviceMetaStore
from src.camera.frame_hub import FrameHub
from src.camera.stereo_feed import StereoFeed


def _native_wh(bgr: Any) -> Optional[Tuple[int, int]]:
    try:
        h, w = int(bgr.shape[0]), int(bgr.shape[1])
        return (w, h) if w > 0 and h > 0 else None
    except Exception:
        return None


class CapturePool:
    """Own thread per camera device; publishes into ``FrameHub``."""

    def __init__(
        self,
        hub: FrameHub,
        device_meta: Optional[DeviceMetaStore] = None,
        **kwargs: Any,
    ) -> None:
        self.hub = hub
        # Accept legacy device_fps= kwarg from older call sites.
        legacy = kwargs.pop("device_fps", None)
        if kwargs:
            raise TypeError(f"unexpected kwargs: {sorted(kwargs)}")
        store = device_meta if device_meta is not None else legacy
        self.device_meta = store if store is not None else DeviceMetaStore()
        self._stop = threading.Event()
        self._threads: List[threading.Thread] = []
        self._stereo_feed: Optional[StereoFeed] = None
        self._stereo_worker: Any = None

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
        self.device_meta.clear()
        self._stereo_worker = stereo
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
        self._stereo_worker = None
        for t in self._threads:
            t.join(timeout=1.0)
        self._threads = []
        self.hub.clear()
        self.device_meta.clear()

    def _rs_loop(self, camera: Any, period: float) -> None:
        while not self._stop.is_set():
            t0 = time.monotonic()
            try:
                frames = camera.read() or {}
            except Exception as e:
                logger.warning("RealSense capture: {}", e)
                frames = {}
            # Native IR → stereo before hub downscale (preview is 640 max side).
            w = self._stereo_worker
            if w is not None:
                ir1, ir2 = frames.get("ir1"), frames.get("ir2")
                if ir1 is not None and ir2 is not None:
                    w.submit(ir1, ir2)
            fps_map = getattr(camera, "last_device_fps", {}) or {}
            for key, bgr in frames.items():
                self.hub.publish(key, bgr)
                self.device_meta.set_fps(key, fps_map.get(key))
                self.device_meta.set_size(key, _native_wh(bgr))
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
                fps_map = getattr(omron, "last_device_fps", {}) or {}
                size_map = getattr(omron, "last_native_size", {}) or {}
                self.device_meta.set_fps(cid, fps_map.get(cid))
                self.device_meta.set_size(cid, size_map.get(cid))
            self._sleep(omron_period, t0)

    @staticmethod
    def _sleep(period: float, t0: float) -> None:
        dt = period - (time.monotonic() - t0)
        if dt > 0:
            time.sleep(dt)
