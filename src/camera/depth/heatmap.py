"""Shared jet heatmap for stereo depth (metres; 0 = invalid)."""

from __future__ import annotations

import cv2
import numpy as np


def depth_to_jet_heatmap(depth: np.ndarray) -> np.ndarray:
    """HxW float32 depth (0 = invalid) -> HxWx3 uint8 BGR jet heatmap."""
    valid = depth > 0
    heatmap = np.zeros((*depth.shape, 3), dtype=np.uint8)
    if not valid.any():
        return heatmap
    d_min = float(depth[valid].min())
    d_max = float(depth[valid].max())
    scale = 255.0 / (d_max - d_min) if d_max > d_min else 0.0
    normalized = np.zeros_like(depth, dtype=np.uint8)
    normalized[valid] = ((depth[valid] - d_min) * scale).astype(np.uint8)
    heatmap = cv2.applyColorMap(normalized, cv2.COLORMAP_JET)
    heatmap[~valid] = 0
    return heatmap


def to_gray_uint8(image: np.ndarray) -> np.ndarray:
    """Coerce BGR/gray frame to HxW uint8 grayscale."""
    if image.ndim == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if image.dtype != np.uint8:
        image = image.astype(np.uint8)
    return image
