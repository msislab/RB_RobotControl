"""ONNX Runtime backend for Fast-FoundationStereo single-file exports."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
import yaml
from loguru import logger

from src.camera.depth.heatmap import depth_to_jet_heatmap, to_gray_uint8
from src.utils.color import green

logger = logger.bind(component="stereo")

IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)
WEIGHTS_DIR = Path(__file__).resolve().parent.parents[2] / "data" / "Fast-FoundationStereo_weights"


class OnnxDepthEstimator:
    """ORT single-ONNX estimator; same ``process`` contract as DepthEstimator."""

    def __init__(
        self,
        *,
        variant: str = "23-36-37",
        onnx_size: str = "576x960",
        valid_iters: int = 4,
        z_far: float = 1.0,
        min_disparity: float = 0.5,
    ) -> None:
        import onnxruntime as ort

        self.z_far = float(z_far)
        self.min_disparity = float(min_disparity)
        self.last_inference_ms = 0.0
        onnx_path = self._resolve_onnx(variant, onnx_size, valid_iters)
        cfg_path = onnx_path.with_suffix(".yaml")
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        self.target_h, self.target_w = int(cfg["image_size"][0]), int(cfg["image_size"][1])

        providers = []
        if "CUDAExecutionProvider" in ort.get_available_providers():
            providers.append("CUDAExecutionProvider")
        providers.append("CPUExecutionProvider")
        logger.info(green(f"Loading ONNX stereo: {onnx_path} providers={providers}"))
        self.session = ort.InferenceSession(str(onnx_path), providers=providers)
        self.input_names = [i.name for i in self.session.get_inputs()]
        self.output_names = [o.name for o in self.session.get_outputs()]

    @staticmethod
    def _resolve_onnx(variant: str, onnx_size: str, valid_iters: int) -> Path:
        # Folder uses underscores: 23_36_37
        folder = variant.replace("-", "_")
        name = f"{folder}_iters_{int(valid_iters)}_res_{onnx_size}.onnx"
        path = WEIGHTS_DIR / "onnx" / folder / onnx_size / name
        if not path.exists():
            raise FileNotFoundError(f"ONNX stereo export not found: {path}")
        if not path.with_suffix(".yaml").exists():
            raise FileNotFoundError(f"ONNX stereo yaml not found: {path.with_suffix('.yaml')}")
        return path

    def _preprocess(self, left: np.ndarray, right: np.ndarray):
        left = to_gray_uint8(left)
        right = to_gray_uint8(right)
        left = np.stack([left, left, left], axis=2)
        right = np.stack([right, right, right], axis=2)
        orig_h, orig_w = left.shape[:2]
        scale_x = self.target_w / float(orig_w)
        if (orig_h, orig_w) != (self.target_h, self.target_w):
            left = cv2.resize(left, (self.target_w, self.target_h), interpolation=cv2.INTER_LINEAR)
            right = cv2.resize(right, (self.target_w, self.target_h), interpolation=cv2.INTER_LINEAR)
        def _norm(img: np.ndarray) -> np.ndarray:
            x = (img.astype(np.float32) / 255.0 - IMAGENET_MEAN) / IMAGENET_STD
            return np.transpose(x, (2, 0, 1))[None].astype(np.float32)
        return _norm(left), _norm(right), scale_x

    def process(
        self,
        left_image: np.ndarray,
        right_image: np.ndarray,
        fx: float,
        baseline: float,
        *,
        with_heatmap: bool = True,
    ) -> Tuple[Optional[np.ndarray], np.ndarray]:
        if fx <= 0 or baseline <= 0:
            raise ValueError(f"fx and baseline must be positive, got fx={fx}, baseline={baseline}")
        t_left, t_right, scale_x = self._preprocess(left_image, right_image)
        feed = {}
        for name in self.input_names:
            if "left" in name.lower():
                feed[name] = t_left
            else:
                feed[name] = t_right
        t0 = time.perf_counter()
        outs = self.session.run(self.output_names, feed)
        self.last_inference_ms = (time.perf_counter() - t0) * 1000.0
        disp = np.asarray(outs[0], dtype=np.float32).reshape(self.target_h, self.target_w)
        disp = np.clip(disp, 0, None) * (1.0 / scale_x)
        # Scale fx to resized width for triangulation at model resolution.
        fx_scaled = float(fx) * scale_x
        valid = disp > self.min_disparity
        depth = np.zeros_like(disp, dtype=np.float32)
        depth[valid] = (fx_scaled * baseline) / disp[valid]
        depth[depth > self.z_far] = 0.0
        # Resize depth back to original IR size for display consistency.
        oh, ow = to_gray_uint8(left_image).shape[:2]
        if depth.shape != (oh, ow):
            depth = cv2.resize(depth, (ow, oh), interpolation=cv2.INTER_NEAREST)
        if not with_heatmap:
            return None, depth
        return depth_to_jet_heatmap(depth), depth
