"""Build stereo depth estimator from config dict."""

from __future__ import annotations

from typing import Any, Dict, Mapping


def build_estimator(cfg: Mapping[str, Any], *, width: int, height: int):
    """Return pytorch or onnx estimator. Raises on missing deps/weights."""
    backend = str(cfg.get("backend", "pytorch")).strip().lower()
    variant = str(cfg.get("variant", "23-36-37"))
    valid_iters = int(cfg.get("valid_iters", 4))
    max_disparity = int(cfg.get("max_disparity", 192))
    z_far = float(cfg.get("z_far", 1.0))
    common: Dict[str, Any] = {
        "variant": variant,
        "valid_iters": valid_iters,
        "max_disparity": max_disparity,
        "z_far": z_far,
    }
    if backend == "pytorch":
        from src.camera.depth.depth import DepthEstimator
        from src.camera.depth.torch_size import pytorch_infer_hw

        ih, iw = pytorch_infer_hw(height, width)
        return DepthEstimator(input_h=ih, input_w=iw, **common)
    if backend == "onnx":
        from src.camera.depth.onnx_depth import OnnxDepthEstimator

        return OnnxDepthEstimator(onnx_size=str(cfg.get("onnx_size", "320x736")), **common)
    raise ValueError(f"Unknown stereo backend {backend!r} (expected pytorch|onnx)")
