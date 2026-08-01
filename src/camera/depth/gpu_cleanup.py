"""Release unused CUDA cache without destroying loaded models/sessions."""

from __future__ import annotations

import gc
from typing import Any, List, Mapping


def release_gpu_cache() -> None:
    """Return freeable CUDA blocks to the driver; keep ORT/torch models intact."""
    gc.collect()
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.synchronize()
            torch.cuda.empty_cache()
    except Exception:
        pass


def shrink_ort_cuda_arena(
    session: Any, output_names: List[str], feed: Mapping[str, Any]
) -> None:
    """One ORT Run that returns unused CUDA arena chunks (keeps the session)."""
    import onnxruntime as ort

    ro = ort.RunOptions()
    ro.add_run_config_entry("memory.enable_memory_arena_shrinkage", "gpu:0")
    session.run(list(output_names), dict(feed), ro)
