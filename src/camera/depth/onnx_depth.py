"""ONNX Runtime backend for Fast-FoundationStereo single-file exports."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, Optional, Tuple

import cv2
import numpy as np
import yaml
from loguru import logger

from src.camera.depth.gpu_cleanup import release_gpu_cache, shrink_ort_cuda_arena
from src.camera.depth.heatmap import depth_to_jet_heatmap, to_gray_uint8
from src.camera.depth.letterbox import letterbox_gray
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
            # ORT≥1.20: DEFAULT == cuDNN FALLBACK ("May be extremely slow").
            # EXHAUSTIVE picks real algos (first run pays search cost → warmup below).
            providers.append(
                (
                    "CUDAExecutionProvider",
                    {
                        "arena_extend_strategy": "kSameAsRequested",
                        # EXHAUSTIVE picks real algos; max_workspace=1 fills VRAM
                        # during search and the arena does not shrink → live OOM.
                        "cudnn_conv_algo_search": "EXHAUSTIVE",
                        "cudnn_conv_use_max_workspace": "0",
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
        self._warmup()

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

    def _warmup(self, iterations: int = 2) -> None:
        """Dummy forwards for EXHAUSTIVE search; shrink arena; keep same session."""
        dummy = np.zeros((self.target_h, self.target_w), dtype=np.uint8)
        t0 = time.perf_counter()
        try:
            for _ in range(max(1, iterations)):
                self.process(dummy, dummy, fx=640.0, baseline=0.05, with_heatmap=False)
            # Algo search peaks VRAM; shrink unused arena chunks, keep session.
            t_left, t_right, *_ = self._preprocess(dummy, dummy)
            feed: Dict[str, np.ndarray] = {
                n: (t_left if "left" in n.lower() else t_right) for n in self.input_names
            }
            shrink_ort_cuda_arena(self.session, self.output_names, feed)
            logger.info(
                green(
                    f"ONNX stereo warmup done in {time.perf_counter() - t0:.1f}s "
                    f"(last {self.last_inference_ms:.0f} ms)"
                )
            )
        except Exception as e:
            logger.warning(yellow(f"ONNX stereo warmup failed (continuing): {e}"))
        finally:
            del dummy
            release_gpu_cache()

    @staticmethod
    def _norm_rgb(gray_u8: np.ndarray) -> np.ndarray:
        rgb = np.stack([gray_u8, gray_u8, gray_u8], axis=2)
        x = (rgb.astype(np.float32) / 255.0 - IMAGENET_MEAN) / IMAGENET_STD
        return np.transpose(x, (2, 0, 1))[None].astype(np.float32)

    def _preprocess(self, left: np.ndarray, right: np.ndarray):
        left = to_gray_uint8(left)
        right = to_gray_uint8(right)
        if left.shape != right.shape:
            raise ValueError(f"IR shape mismatch: {left.shape} vs {right.shape}")
        oh, ow = left.shape[:2]
        left_p, scale, ch, cw = letterbox_gray(left, self.target_h, self.target_w)
        right_p, scale_r, ch_r, cw_r = letterbox_gray(right, self.target_h, self.target_w)
        if (ch, cw, scale) != (ch_r, cw_r, scale_r):
            raise RuntimeError("left/right letterbox scales differ")
        return self._norm_rgb(left_p), self._norm_rgb(right_p), scale, ch, cw, oh, ow

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
        t_left, t_right, scale, ch, cw, oh, ow = self._preprocess(left_image, right_image)
        feed = {}
        for name in self.input_names:
            feed[name] = t_left if "left" in name.lower() else t_right
        t0 = time.perf_counter()
        outs = self.session.run(self.output_names, feed)
        self.last_inference_ms = (time.perf_counter() - t0) * 1000.0
        disp = np.asarray(outs[0], dtype=np.float32).reshape(self.target_h, self.target_w)
        disp = np.clip(disp[:ch, :cw], 0, None)
        # Model-space disp + fx scaled by letterbox scale (do not also rescale disp).
        fx_m = float(fx) * float(scale)
        valid = disp > self.min_disparity
        depth_s = np.zeros((ch, cw), dtype=np.float32)
        depth_s[valid] = (fx_m * baseline) / disp[valid]
        depth_s[depth_s > self.z_far] = 0.0
        depth = (
            depth_s
            if (ch, cw) == (oh, ow)
            else cv2.resize(depth_s, (ow, oh), interpolation=cv2.INTER_NEAREST)
        )
        if not with_heatmap:
            return None, depth
        return depth_to_jet_heatmap(depth), depth
