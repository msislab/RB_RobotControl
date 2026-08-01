"""Grab latest Omron frame; drain stream backlog to cut preview lag."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from src.camera.preview_scale import downscale_preview

DeviceRow = Tuple[str, Any, Any, Any]
NativeSize = Tuple[int, int]


def latest_bgr(
    stream: Any,
    converter: Any,
    *,
    timeout_ms: int,
) -> Tuple[Optional[np.ndarray], Optional[NativeSize]]:
    """Return (preview BGR, native WxH); full ROI discarded after resize."""
    try:
        buffer = stream.retrieve_buffer(timeout=timeout_ms)
    except Exception:
        return None, None
    if buffer is None:
        return None, None
    while True:
        try:
            nxt = stream.retrieve_buffer(timeout=1)
        except Exception:
            break
        if nxt is None:
            break
        buffer = nxt
    image = converter.convert(buffer.get_image())
    data = np.frombuffer(image.get_image_data(), dtype=np.uint8)
    w, h = int(image.width), int(image.height)
    bgr = data.reshape((h, w, 3))
    return downscale_preview(bgr), (w, h)


def read_one(
    devices: List[DeviceRow], cid: str, *, timeout_ms: int
) -> Tuple[Optional[np.ndarray], Optional[NativeSize]]:
    for row_cid, _device, stream, converter in devices:
        if row_cid == cid:
            return latest_bgr(stream, converter, timeout_ms=timeout_ms)
    raise KeyError(f"Unknown Omron camera id: {cid}")


def read_all(
    devices: List[DeviceRow], *, timeout_ms: int
) -> Dict[str, np.ndarray]:
    out: Dict[str, np.ndarray] = {}
    for cid, _device, stream, converter in devices:
        bgr, _size = latest_bgr(stream, converter, timeout_ms=timeout_ms)
        if bgr is not None:
            out[cid] = bgr
    return out
