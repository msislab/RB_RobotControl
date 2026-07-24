"""One worker thread per preview pane: wait for new frames, schedule Tk apply."""

from __future__ import annotations

import threading
from typing import Any, Callable, Dict, List, Optional, Sequence

from loguru import logger

from src.camera.frame_hub import FrameHub
from src.camera.gui_preview import fit_bgr, update_one_image


class PaneWorkerPool:
    """Per-key threads; image apply runs on the Tk thread via ``schedule``."""

    def __init__(
        self,
        hub: FrameHub,
        *,
        schedule: Callable[[Callable[[], None]], None],
        get_frames: Callable[[], Dict[str, Any]],
        get_labels: Callable[[], Dict[str, Any]],
        get_photo: Callable[[], Dict[str, Any]],
        on_frame: Callable[[str], None],
        hide_preview: Optional[Callable[[], bool]] = None,
        clear_image: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.hub = hub
        self._schedule = schedule
        self._get_frames = get_frames
        self._get_labels = get_labels
        self._get_photo = get_photo
        self._on_frame = on_frame
        self._hide_preview = hide_preview or (lambda: False)
        self._clear_image = clear_image
        self._stop = threading.Event()
        self._threads: List[threading.Thread] = []
        self._lock = threading.Lock()
        self._latest: Dict[str, Any] = {}
        self._pending: set[str] = set()
        self._blanked: set[str] = set()

    def start(self, keys: Sequence[str]) -> None:
        self.stop()
        self._stop.clear()
        self._blanked.clear()
        for key in keys:
            t = threading.Thread(
                target=self._loop,
                args=(key,),
                name=f"pane-{key}",
                daemon=True,
            )
            self._threads.append(t)
            t.start()
        logger.info("PaneWorkerPool started ({} panes)", len(self._threads))

    def stop(self) -> None:
        self._stop.set()
        for t in self._threads:
            t.join(timeout=1.0)
        self._threads = []
        with self._lock:
            self._latest.clear()
            self._pending.clear()

    def add_key(self, key: str) -> None:
        if any(t.name == f"pane-{key}" and t.is_alive() for t in self._threads):
            return
        t = threading.Thread(
            target=self._loop, args=(key,), name=f"pane-{key}", daemon=True
        )
        self._threads.append(t)
        t.start()

    def _loop(self, key: str) -> None:
        gen = 0
        while not self._stop.is_set():
            if self._hide_preview():
                gen2 = self.hub.wait_new_gen(key, gen, timeout=0.25)
                if gen2 == gen or self._stop.is_set():
                    continue
                gen = gen2
                self._schedule(lambda k=key: self._tick_fps_only(k))
                continue
            frame, gen = self.hub.wait_new(key, gen, timeout=0.25)
            if frame is None or self._stop.is_set():
                continue
            with self._lock:
                self._latest[key] = frame
                if key in self._pending:
                    continue
                self._pending.add(key)
            self._schedule(lambda k=key: self._apply_latest(k))

    def _tick_fps_only(self, key: str) -> None:
        if self._stop.is_set():
            return
        if key not in self._blanked and self._clear_image is not None:
            self._clear_image(key)
            self._blanked.add(key)
        self._on_frame(key)

    def _apply_latest(self, key: str) -> None:
        with self._lock:
            self._pending.discard(key)
            bgr = self._latest.pop(key, None)
        if bgr is None or self._stop.is_set():
            return
        if self._hide_preview():
            self._tick_fps_only(key)
            return
        self._blanked.discard(key)
        frames = self._get_frames()
        labels = self._get_labels()
        if key not in labels:
            return
        fitted = fit_bgr(bgr, frames, key)
        update_one_image(labels, self._get_photo(), key, fitted)
        self._on_frame(key)
