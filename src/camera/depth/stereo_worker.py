"""Background stereo load + latest-frame inference worker."""

from __future__ import annotations

import threading
from typing import Any, Dict, Mapping, Optional, Tuple

import numpy as np
from loguru import logger

from src.camera.depth.factory import build_estimator
from src.utils.color import green, red, yellow

logger = logger.bind(component="stereo")


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
            est = build_estimator(self.stereo_cfg, width=self.width, height=self.height)
            if self._stop.is_set():
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

    def submit(self, ir1: np.ndarray, ir2: np.ndarray) -> None:
        if not self._ready or self._stop.is_set():
            return
        with self._lock:
            self._pending = (ir1.copy(), ir2.copy())

    def latest_heatmap(self) -> Optional[np.ndarray]:
        with self._lock:
            return None if self._heatmap is None else self._heatmap.copy()

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
            try:
                heatmap, _ = self._estimator.process(
                    pair[0], pair[1], self.fx, self.baseline, with_heatmap=True
                )
                if heatmap is not None:
                    with self._lock:
                        self._heatmap = heatmap
            except Exception as exc:
                logger.warning(yellow(f"Stereo infer failed: {exc}"))

    def stop(self) -> None:
        self._stop.set()
        for t in (self._load_thread, self._loop_thread):
            if t is not None and t.is_alive():
                t.join(timeout=2.0)
        self._estimator = None
        self._ready = False
