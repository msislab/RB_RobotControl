"""Aspect-preserving resize + pad for fixed-size stereo ONNX inputs."""

from __future__ import annotations

from typing import Tuple

import cv2
import numpy as np


def letterbox_gray(
    gray: np.ndarray, target_h: int, target_w: int
) -> Tuple[np.ndarray, float, int, int]:
    """Uniform scale into ``target_h×target_w`` with right/bottom replicate pad.

    Returns ``(padded, scale, content_h, content_w)``.
    """
    h, w = int(gray.shape[0]), int(gray.shape[1])
    if h <= 0 or w <= 0:
        raise ValueError(f"invalid gray shape {gray.shape}")
    scale = min(target_w / float(w), target_h / float(h))
    cw = max(1, int(round(w * scale)))
    ch = max(1, int(round(h * scale)))
    scaled = cv2.resize(gray, (cw, ch), interpolation=cv2.INTER_LINEAR)
    pad_b = target_h - ch
    pad_r = target_w - cw
    padded = cv2.copyMakeBorder(
        scaled, 0, pad_b, 0, pad_r, borderType=cv2.BORDER_REPLICATE
    )
    return padded, float(scale), ch, cw
