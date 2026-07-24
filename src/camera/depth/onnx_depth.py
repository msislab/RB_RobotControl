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
from src.camera.depth.ort_cuda_libs import ensure_nvidia_lib_path
from src.utils.color import green, yellow

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
        onnx_size: str = "320x736",
        valid_iters: int = 4,
        max_disparity: int = 192,
        z_far: float = 1.0,
        min_disparity: float = 0.5,
    ) -> None:
        ensure_nvidia_lib_path()
        try:
            import onnxruntime as ort
        except ImportError as e:
            raise ImportError(
                "ONNX stereo needs onnxruntime-gpu (CUDA 12.x wheel, e.g. "
                "onnxruntime-gpu==1.22.0). Install: pip install -r requirements-stereo.txt"
            ) from e

        self.z_far = float(z_far)
        self.min_disparity = float(min_disparity)
        self.max_disparity = int(max_disparity)
        self.last_inference_ms = 0.0
        onnx_path = self._resolve_onnx(variant, onnx_size, valid_iters)
        with open(onnx_path.with_suffix(".yaml"), "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        self.target_h, self.target_w = int(cfg["image_size"][0]), int(cfg["image_size"][1])

        available = ort.get_available_providers()
        providers: list = []
        if "CUDAExecutionProvider" in available:
            providers.append(
                (
                    "CUDAExecutionProvider",
                    {
                        "arena_extend_strategy": "kSameAsRequested",
                        "cudnn_conv_algo_search": "DEFAULT",
                    },
                )
            )
        else:
            logger.warning(yellow("CUDAExecutionProvider missing — ONNX stereo on CPU"))
        providers.append("CPUExecutionProvider")
        so = ort.SessionOptions()
        so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        logger.info(green(f"Loading ONNX stereo: {onnx_path} providers={providers}"))
        try:
            self.session = ort.InferenceSession(
                str(onnx_path), sess_options=so, providers=providers
            )
        except Exception as e:
            if "CUDAExecutionProvider" not in available:
                raise
            logger.warning(yellow(f"CUDA ONNX session failed ({e}); retrying CPU"))
            self.session = ort.InferenceSession(
                str(onnx_path), sess_options=so, providers=["CPUExecutionProvider"]
            )
        self.input_names = [i.name for i in self.session.get_inputs()]
        self.output_names = [o.name for o in self.session.get_outputs()]
        logger.info(green(f"ONNX stereo session providers={self.session.get_providers()}"))

    @staticmethod
    def _resolve_onnx(variant: str, onnx_size: str, valid_iters: int) -> Path:
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
            feed[name] = t_left if "left" in name.lower() else t_right
        t0 = time.perf_counter()
        outs = self.session.run(self.output_names, feed)
        self.last_inference_ms = (time.perf_counter() - t0) * 1000.0
        disp = np.asarray(outs[0], dtype=np.float32).reshape(self.target_h, self.target_w)
        disp = np.clip(disp, 0, None) * (1.0 / scale_x)
        fx_scaled = float(fx) * scale_x
        valid = disp > self.min_disparity
        depth = np.zeros_like(disp, dtype=np.float32)
        depth[valid] = (fx_scaled * baseline) / disp[valid]
        depth[depth > self.z_far] = 0.0
        oh, ow = to_gray_uint8(left_image).shape[:2]
        if depth.shape != (oh, ow):
            depth = cv2.resize(depth, (ow, oh), interpolation=cv2.INTER_NEAREST)
        if not with_heatmap:
            return None, depth
        return depth_to_jet_heatmap(depth), depth
