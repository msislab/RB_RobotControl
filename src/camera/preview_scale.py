"""Shared preview scaling — keep Tk off full-resolution camera frames."""

from __future__ import annotations

import cv2
import numpy as np

# Pane display budget (long side). Capture may be larger; hub downscales here.
PREVIEW_MAX_SIDE = 640


def downscale_preview(bgr: np.ndarray, max_side: int = PREVIEW_MAX_SIDE) -> np.ndarray:
    """Return a preview-sized BGR image (new array)."""
    if bgr is None or bgr.size == 0:
        return bgr
    h, w = bgr.shape[:2]
    m = max(h, w)
    if m <= max_side:
        return np.ascontiguousarray(bgr)
    scale = max_side / float(m)
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    return cv2.resize(bgr, (nw, nh), interpolation=cv2.INTER_AREA)
