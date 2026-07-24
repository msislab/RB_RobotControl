"""Thin Omron/StApi multi-camera capture for live RGB display."""

from __future__ import annotations

import time
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from loguru import logger

from src.camera.omron_frame import read_all as frames_all, read_one as frame_one
from src.camera.omron_fps import OmronResultingFps
from src.camera.omron_gain import clamp_gain, get_omron_gain_limits, probe_gain_limits
from src.camera.omron_net import auto_assign_ips
from src.camera.omron_nodes import set_enumeration, set_numeric
from src.camera.omron_open import open_freerun
from src.utils.color import green, red, yellow

try:
    import stapipy as st
except ImportError:  # pragma: no cover
    st = None  # type: ignore

DeviceRow = Tuple[str, Any, Any, Any]  # cid, device, stream, converter

_st_lock = Lock()
_st_ready = False
_network_prepared = False
_shared_system: Any = None
_device_pool: List[DeviceRow] = []
_pool_lock = Lock()

__all__ = [
    "OmronCameras",
    "get_omron_gain_limits",
    "open_omron_devices_at_startup",
    "prepare_omron_network",
    "shutdown_omron_devices",
]


def _ensure_stapi() -> Any:
    if st is None:
        raise RuntimeError("stapipy is not installed (Omron/StApi SDK required)")
    global _st_ready
    with _st_lock:
        if not _st_ready:
            st.initialize()
            _st_ready = True
            logger.info("STApi initialized for Omron cameras")
        return st


def prepare_omron_network(
    ip_pool_cidr: str,
    preferred_ips: Optional[List[str]] = None,
) -> None:
    """ForceIP assignment — call once at process start."""
    global _network_prepared, _shared_system
    if _network_prepared:
        return
    t0 = time.monotonic()
    api = _ensure_stapi()
    _shared_system = api.create_system()
    auto_assign_ips(
        api, _shared_system, ip_pool_cidr=ip_pool_cidr, preferred=list(preferred_ips or [])
    )
    _network_prepared = True
    logger.info(green(f"Omron IP assignment finished at startup ({time.monotonic() - t0:.2f}s)"))


def open_omron_devices_at_startup(
    *,
    exposure: float = 500.0,
    gain: float = 200.0,
) -> int:
    """Enumerate + start_acquisition for all cameras at process start."""
    global _device_pool, _shared_system
    with _pool_lock:
        if _device_pool:
            return len(_device_pool)
        t0 = time.monotonic()
        api = _ensure_stapi()
        if _shared_system is None:
            _shared_system = api.create_system()
        devices: List[Any] = []
        for _ in range(32):
            try:
                devices.append(_shared_system.create_first_device())
            except Exception:
                break
        if not devices:
            raise RuntimeError("No Omron cameras found at startup")
        probe_gain_limits(api, devices[0])
        gain = clamp_gain(gain)
        logger.info("Omron opening {} device(s) at process start…", len(devices))
        _device_pool = [
            open_freerun(
                api, i, device, exposure=float(exposure), gain=float(gain), detail=(i == 0)
            )
            for i, device in enumerate(devices)
        ]
        n = len(_device_pool)
        logger.info(green(f"Omron devices ready at startup: {n} ({time.monotonic() - t0:.2f}s)"))
        return n


def shutdown_omron_devices() -> None:
    """Stop acquisition for the process-wide pool (window close / exit)."""
    global _device_pool
    with _pool_lock:
        rows = list(_device_pool)
        _device_pool = []
    for cid, device, stream, _conv in rows:
        try:
            device.acquisition_stop()
        except Exception:
            logger.exception("acquisition_stop failed for {}", cid)
        try:
            stream.stop_acquisition()
        except Exception:
            logger.exception("datastream stop failed for {}", cid)
    if rows:
        logger.info(red("Omron device pool shut down"))


class OmronCameras:
    """Attach to process-start device pool for live RGB preview."""

    def __init__(
        self,
        *,
        exposure: float = 500.0,
        gain: float = 200.0,
        timeout_ms: int = 50,
    ) -> None:
        self.exposure = float(exposure)
        self.gain = float(gain)
        self.timeout_ms = timeout_ms
        self._devices: List[DeviceRow] = []
        self._resulting_fps = OmronResultingFps()
        self.last_device_fps: Dict[str, Optional[float]] = {}

    @property
    def camera_ids(self) -> List[str]:
        return [cid for cid, *_ in self._devices]

    def start(self) -> None:
        """Borrow already-open pool (no start_acquisition here)."""
        if self._devices:
            return
        with _pool_lock:
            empty = not _device_pool
        if empty:
            logger.warning("Omron pool empty — opening devices now (slow path)")
            open_omron_devices_at_startup(exposure=self.exposure, gain=self.gain)
        with _pool_lock:
            if not _device_pool:
                raise RuntimeError("Omron devices not available")
            self._devices = list(_device_pool)
        self.set_exposure_gain(self.exposure, self.gain)
        logger.info(green(f"Omron attached to {len(self._devices)} device(s)"))

    def stop(self) -> None:
        """Detach from GUI only — pool keeps streaming for fast re-Start."""
        self._devices = []
        self.last_device_fps = {}
        logger.info(yellow("Omron detached (devices stay open from startup)"))

    def set_exposure_gain(self, exposure: float, gain: float) -> None:
        self.exposure = float(exposure)
        self.gain = clamp_gain(gain)
        api = _ensure_stapi()
        with _pool_lock:
            rows = list(self._devices) if self._devices else list(_device_pool)
        for cid, device, _stream, _conv in rows:
            try:
                nodemap = device.remote_port.nodemap
                set_enumeration(api, nodemap, "GainAuto", "Off")
                set_enumeration(api, nodemap, "ExposureAuto", "Off")
                set_numeric(api, nodemap, "Gain", self.gain)
                set_numeric(api, nodemap, "ExposureTime", self.exposure)
            except Exception:
                logger.exception("Omron exposure/gain failed for {}", cid)

    def read_one(self, cid: str) -> Optional[np.ndarray]:
        if not self._devices:
            raise RuntimeError("Omron cameras not attached")
        bgr = frame_one(self._devices, cid, timeout_ms=self.timeout_ms)
        if bgr is not None:
            self.last_device_fps[cid] = self._resulting_fps.touch(
                _ensure_stapi(), self._devices, cid
            )
        return bgr

    def read_all(self) -> Dict[str, np.ndarray]:
        if not self._devices:
            raise RuntimeError("Omron cameras not attached")
        return frames_all(self._devices, timeout_ms=self.timeout_ms)
