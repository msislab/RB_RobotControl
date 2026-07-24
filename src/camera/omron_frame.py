"""Grab latest Omron frame; drain stream backlog to cut preview lag."""

from __future__ import annotations

from typing import Any, Optional

import numpy as np


def latest_bgr(
    stream: Any,
    converter: Any,
    *,
    timeout_ms: int,
) -> Optional[np.ndarray]:
    """Return newest full-res BGR frame, dropping older queued buffers."""
    try:
        buffer = stream.retrieve_buffer(timeout=timeout_ms)
    except Exception:
        return None
    if buffer is None:
        return None
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
    return data.reshape((int(image.height), int(image.width), 3)).copy()
