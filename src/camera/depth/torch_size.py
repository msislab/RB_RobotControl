"""Cap pytorch stereo infer size so ~8GB GPUs do not OOM at 1280×720."""

from __future__ import annotations

from typing import Tuple

import cv2
import numpy as np

from src.camera.depth.heatmap import to_gray_uint8
from src.camera.depth.letterbox import letterbox_gray

# Full-res IR (1280×720) needs ~4GiB extra activations → OOM on 8GB cards.
_PYTORCH_MAX_SIDE = 640


def pytorch_infer_hw(height: int, width: int) -> Tuple[int, int]:
    """Return (h, w) for warmup/live infer, capped by max side."""
    h, w = int(height), int(width)
    m = max(h, w)
    if m <= _PYTORCH_MAX_SIDE:
        return h, w
    s = _PYTORCH_MAX_SIDE / float(m)
    return max(1, int(round(h * s))), max(1, int(round(w * s)))


def letterbox_ir_pair(
    left_image: np.ndarray, right_image: np.ndarray, target_h: int, target_w: int
) -> Tuple[np.ndarray, np.ndarray, float, int, int, int, int]:
    """Gray + letterbox both IRs. Returns left_p, right_p, scale, ch, cw, oh, ow."""
    left = to_gray_uint8(left_image)
    right = to_gray_uint8(right_image)
    if left.shape != right.shape:
        raise ValueError(f"IR shape mismatch: {left.shape} vs {right.shape}")
    oh, ow = left.shape[:2]
    left_p, scale, ch, cw = letterbox_gray(left, target_h, target_w)
    right_p, scale_r, ch_r, cw_r = letterbox_gray(right, target_h, target_w)
    if (ch, cw, scale) != (ch_r, cw_r, scale_r):
        raise RuntimeError("left/right letterbox scales differ")
    return left_p, right_p, float(scale), ch, cw, oh, ow


def depth_from_letterbox(
    depth_lb: np.ndarray, ch: int, cw: int, oh: int, ow: int
) -> np.ndarray:
    depth_s = depth_lb[:ch, :cw]
    if (ch, cw) == (oh, ow):
        return depth_s
    return cv2.resize(depth_s, (ow, oh), interpolation=cv2.INTER_NEAREST)
