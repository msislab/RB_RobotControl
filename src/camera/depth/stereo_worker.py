"""Background stereo load + latest-frame inference worker."""

from __future__ import annotations

import threading
from typing import Any, Dict, Mapping, Optional, Tuple

import numpy as np
from loguru import logger

from src.camera.depth.factory import build_estimator
from src.camera.depth.gpu_cleanup import release_gpu_cache
from src.utils.color import green, red, yellow

logger = logger.bind(component="stereo")

_JOIN_S = 5.0


class StereoWorker:
    """Load estimator on a thread; infer when idle; expose latest heatmap."""

    def __init__(
        self,
        fx: float,
        baseline: float,
        stereo_cfg: Mapping[str, Any],
        *,
        width: int,
        height: int,
    ) -> None:
        self.fx = float(fx)
        self.baseline = float(baseline)
        self.stereo_cfg = dict(stereo_cfg)
        self.width = int(width)
        self.height = int(height)
        self._estimator = None
        self._ready = False
        self._error: Optional[str] = None
        self._heatmap: Optional[np.ndarray] = None
        self._heatmap_dirty = False
        self._pending: Optional[Tuple[np.ndarray, np.ndarray]] = None
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._load_thread: Optional[threading.Thread] = None
        self._loop_thread: Optional[threading.Thread] = None

    @property
    def ready(self) -> bool:
        return self._ready

    @property
    def error(self) -> Optional[str]:
        return self._error

    def start_load(self) -> None:
        self._load_thread = threading.Thread(target=self._load, daemon=True)
        self._load_thread.start()

    def _load(self) -> None:
        try:
            # One load+warmup; live infer reuses this same estimator instance.
            est = build_estimator(self.stereo_cfg, width=self.width, height=self.height)
            if self._stop.is_set():
                del est
                release_gpu_cache()
                return
            self._estimator = est
            self._ready = True
            logger.info(green("Stereo worker ready"))
            self._loop_thread = threading.Thread(target=self._loop, daemon=True)
            self._loop_thread.start()
        except Exception as exc:
            self._error = str(exc)
            self._ready = False
            logger.error(red(f"Stereo load failed: {exc}"))
            release_gpu_cache()

    def submit(self, ir1: np.ndarray, ir2: np.ndarray) -> None:
        if not self._ready or self._stop.is_set():
            return
        with self._lock:
            self._pending = (ir1.copy(), ir2.copy())

    def latest_heatmap(self) -> Optional[np.ndarray]:
        with self._lock:
            return None if self._heatmap is None else self._heatmap.copy()

    def consume_heatmap(self) -> Optional[np.ndarray]:
        """Return a new heatmap once; None if unchanged since last consume."""
        with self._lock:
            if not self._heatmap_dirty or self._heatmap is None:
                return None
            self._heatmap_dirty = False
            return self._heatmap.copy()

    def _loop(self) -> None:
        while not self._stop.is_set():
            pair = None
            with self._lock:
                if self._pending is not None:
                    pair = self._pending
                    self._pending = None
            if pair is None:
                self._stop.wait(0.01)
                continue
            est = self._estimator
            if est is None or self._stop.is_set():
                continue
            try:
                ir_w = int(pair[0].shape[1])
                fx = self.fx * (ir_w / float(self.width)) if self.width > 0 else self.fx
                heatmap, _ = est.process(
                    pair[0], pair[1], fx, self.baseline, with_heatmap=True
                )
                if heatmap is not None and not self._stop.is_set():
                    with self._lock:
                        self._heatmap = heatmap
                        self._heatmap_dirty = True
            except Exception as exc:
                if not self._stop.is_set():
                    logger.warning(yellow(f"Stereo infer failed: {exc}"))

    def stop(self) -> None:
        self._stop.set()
        self._ready = False
        with self._lock:
            self._pending = None
        alive = False
        for t in (self._load_thread, self._loop_thread):
            if t is not None and t.is_alive():
                t.join(timeout=_JOIN_S)
                if t.is_alive():
                    alive = True
        # Never drop ORT/torch session while a thread may still be in process().
        if alive:
            logger.warning(
                yellow("Stereo threads still busy after join — deferring estimator release")
            )
            return
        self._estimator = None
        release_gpu_cache()
