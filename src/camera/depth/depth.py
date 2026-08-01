"""Fast-FoundationStereo DepthEstimator (ported from /MP vision_system_fw)."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import torch
from loguru import logger

from src.camera.depth.gpu_cleanup import release_gpu_cache
from src.camera.depth.heatmap import depth_to_jet_heatmap, to_gray_uint8
from src.utils.color import green, yellow

logger = logger.bind(component="stereo")


class DepthEstimator:
    """PyTorch Fast-FoundationStereo estimator: ``process`` → (heatmap, depth_m)."""

    SCRIPT_DIR = Path(__file__).parent.resolve()
    REPO_DIR_CANDIDATES = (
        SCRIPT_DIR / "Fast-FoundationStereo",
        SCRIPT_DIR / "FastFoundationStereo",
    )
    WEIGHTS_DIR = SCRIPT_DIR.parents[2] / "data" / "Fast-FoundationStereo_weights"
    CHECKPOINT_NAME = "model_best_bp2_serialize.pth"

    def __init__(
        self,
        checkpoint_path: Optional[str] = None,
        *,
        variant: str = "23-36-37",
        valid_iters: int = 4,
        max_disparity: int = 192,
        z_far: float = 1.0,
        min_disparity: float = 0.5,
        warmup: bool = True,
        input_h: int = 360,
        input_w: int = 640,
    ) -> None:
        self.logger = logger
        self.variant = str(variant)
        self.valid_iters = int(valid_iters)
        self.max_disparity = int(max_disparity)
        self.z_far = float(z_far)
        self.min_disparity = float(min_disparity)
        self.input_h = int(input_h)
        self.input_w = int(input_w)
        self.model = None
        self.last_inference_ms = 0.0

        repo_dir = self._resolve_repo_dir()
        checkpoint = Path(checkpoint_path) if checkpoint_path else self._resolve_checkpoint()
        checkpoint = checkpoint.expanduser().resolve()
        if not checkpoint.exists():
            raise FileNotFoundError(f"Stereo checkpoint not found: {checkpoint}")

        weights_dir = self.WEIGHTS_DIR.resolve()
        if weights_dir not in checkpoint.parents and checkpoint.parent != weights_dir:
            raise ValueError(f"Refusing to load checkpoint outside {weights_dir}: {checkpoint}")

        if not torch.cuda.is_available():
            raise RuntimeError("CUDA GPU is required to run Fast-FoundationStereo.")

        if str(repo_dir) not in sys.path:
            sys.path.insert(0, str(repo_dir))
        for alias, target in (("float", float), ("int", int), ("bool", bool), ("object", object)):
            if not hasattr(np, alias):
                setattr(np, alias, target)

        self.logger.info(green(f"Loading stereo checkpoint: {checkpoint}"))
        self.model = torch.load(str(checkpoint), map_location="cpu", weights_only=False)
        self.model.args.valid_iters = self.valid_iters
        self.model.args.max_disp = self.max_disparity
        self.model.cuda().eval()
        self.logger.info(green("Stereo model loaded on GPU."))
        if warmup:
            self._warmup()

    def _resolve_repo_dir(self) -> Path:
        for candidate in self.REPO_DIR_CANDIDATES:
            if candidate.is_dir():
                return candidate
        raise FileNotFoundError(
            "Fast-FoundationStereo repo not found next to this file. "
            f"Expected one of: {', '.join(str(c) for c in self.REPO_DIR_CANDIDATES)}"
        )

    def _resolve_checkpoint(self) -> Path:
        weights_dir = self.WEIGHTS_DIR
        checkpoint = weights_dir / self.variant / self.CHECKPOINT_NAME
        if checkpoint.exists():
            return checkpoint
        if not weights_dir.is_dir():
            raise FileNotFoundError(f"Stereo weights directory not found: {weights_dir}")
        matches = sorted(weights_dir.glob(f"*/{self.CHECKPOINT_NAME}"))
        if matches:
            return matches[0]
        raise FileNotFoundError(f"Stereo checkpoint not found: {checkpoint}")

    def _ir_to_tensor(self, ir: np.ndarray) -> torch.Tensor:
        rgb = np.stack([ir, ir, ir], axis=2)
        t = torch.from_numpy(rgb).permute(2, 0, 1).float()
        return t.unsqueeze(0).cuda()

    def _pad32(self, t: torch.Tensor):
        _, _, h, w = t.shape
        ph = (32 - h % 32) % 32
        pw = (32 - w % 32) % 32
        return torch.nn.functional.pad(t, [0, pw, 0, ph]), h, w

    def _unpad(self, t: torch.Tensor, h: int, w: int) -> torch.Tensor:
        return t[:, :, :h, :w]

    def _warmup(self, iterations: int = 3) -> None:
        dummy = np.zeros((self.input_h, self.input_w), dtype=np.uint8)
        self.logger.info(
            green(
                f"Warming up stereo ({self.input_w}x{self.input_h}, {iterations} forwards)..."
            )
        )
        t0 = time.perf_counter()
        try:
            for _ in range(max(1, iterations)):
                self._infer(dummy, dummy, fx=640.0, baseline=0.018, warmup=True)
            self.logger.info(green(f"Stereo warmup done in {time.perf_counter() - t0:.1f}s"))
        except Exception as e:
            self.logger.warning(yellow(f"Stereo warmup failed (continuing): {e}"))
        finally:
            # Keep this model for live infer; only release unused CUDA cache.
            del dummy
            release_gpu_cache()

    def _infer(
        self,
        left_ir: np.ndarray,
        right_ir: np.ndarray,
        fx: float,
        baseline: float,
        warmup: bool = False,
    ) -> np.ndarray:
        if fx <= 0 or baseline <= 0:
            raise ValueError(f"fx and baseline must be positive, got fx={fx}, baseline={baseline}")
        if self.model is None:
            raise RuntimeError("Stereo model is not loaded.")
        left_ir = to_gray_uint8(left_ir)
        right_ir = to_gray_uint8(right_ir)
        if left_ir.shape != right_ir.shape:
            raise ValueError(f"IR shape mismatch: {left_ir.shape} vs {right_ir.shape}")
        img0p, h, w = self._pad32(self._ir_to_tensor(left_ir))
        img1p, _, _ = self._pad32(self._ir_to_tensor(right_ir))
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        with torch.inference_mode():
            disp_raw = self.model.forward(
                img0p,
                img1p,
                iters=self.valid_iters,
                test_mode=True,
                optimize_build_volume="pytorch1",
            )
        torch.cuda.synchronize()
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        if not warmup:
            self.last_inference_ms = elapsed_ms
        disp = self._unpad(disp_raw, h, w).squeeze().cpu().numpy().astype(np.float32)
        del img0p, img1p, disp_raw
        valid = disp > self.min_disparity
        depth = np.zeros_like(disp, dtype=np.float32)
        depth[valid] = (fx * baseline) / disp[valid]
        depth[depth > self.z_far] = 0.0
        return depth

    def process(
        self,
        left_image: np.ndarray,
        right_image: np.ndarray,
        fx: float,
        baseline: float,
        *,
        with_heatmap: bool = True,
    ) -> Tuple[Optional[np.ndarray], np.ndarray]:
        depth = self._infer(left_image, right_image, fx, baseline)
        if not with_heatmap:
            return None, depth
        return depth_to_jet_heatmap(depth), depth
