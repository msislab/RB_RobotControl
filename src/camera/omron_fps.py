"""Omron GenICam ResultingFrameRate probe (live actual only)."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

from src.camera.omron_nodes import get_numeric

DeviceRow = Tuple[str, Any, Any, Any]


class OmronResultingFps:
    """Throttle ResultingFrameRate reads; remember missing nodes."""

    def __init__(self, period_s: float = 1.0) -> None:
        self._period = float(period_s)
        self._ok: Dict[str, bool] = {}
        self._val: Dict[str, Optional[float]] = {}
        self._t: Dict[str, float] = {}

    def get(self, cid: str) -> Optional[float]:
        return self._val.get(cid)

    def touch(self, api: Any, devices: List[DeviceRow], cid: str) -> Optional[float]:
        if self._ok.get(cid) is False:
            return None
        now = time.monotonic()
        if now - self._t.get(cid, 0.0) < self._period and cid in self._val:
            return self._val.get(cid)
        device = next((d for c, d, *_ in devices if c == cid), None)
        if device is None:
            return self._val.get(cid)
        self._t[cid] = now
        raw = get_numeric(api, device.remote_port.nodemap, "ResultingFrameRate")
        if raw is None:
            if cid not in self._ok:
                self._ok[cid] = False
                self._val[cid] = None
            return None
        self._ok[cid] = True
        fps = float(raw) if float(raw) > 0 else None
        self._val[cid] = fps
        return fps
