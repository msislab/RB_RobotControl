"""Make pip nvidia-* CUDA libs visible for onnxruntime-gpu CUDA EP."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from loguru import logger

from src.utils.color import yellow

_NVIDIA_SUBS = (
    "cuda_runtime/lib",
    "cublas/lib",
    "cudnn/lib",
    "cufft/lib",
    "curand/lib",
    "cusolver/lib",
    "cusparse/lib",
    "cuda_nvrtc/lib",
    "nvjitlink/lib",
    "cuda_cupti/lib",
    "nccl/lib",
)


def ensure_nvidia_lib_path() -> None:
    try:
        import nvidia  # type: ignore
    except Exception:
        return
    root = Path(nvidia.__file__).resolve().parent
    extras: List[str] = [str(root / s) for s in _NVIDIA_SUBS if (root / s).is_dir()]
    if not extras:
        return
    cur = [p for p in os.environ.get("LD_LIBRARY_PATH", "").split(":") if p]
    os.environ["LD_LIBRARY_PATH"] = ":".join(extras + [p for p in cur if p not in extras])
    try:
        import ctypes

        for sub in extras:
            for lib in sorted(Path(sub).glob("lib*.so*")):
                if not lib.is_file():
                    continue
                try:
                    ctypes.CDLL(str(lib), mode=ctypes.RTLD_GLOBAL)
                except OSError:
                    pass
    except Exception as e:
        logger.warning(yellow(f"NVIDIA lib preload skipped: {e}"))
