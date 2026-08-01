"""Shared go-home helper for graceful stop paths."""

from __future__ import annotations

from typing import Any

import numpy as np
from loguru import logger

from src.config.loader import MOTION_HOME
from src.utils.color import green, yellow


def go_home(app: Any, *, speed: float = 100.0, acc: float = 500.0) -> None:
    """TCP move to motion home (skipped if immediate stop already set)."""
    if getattr(app, "immediate_stop", False):
        logger.info(yellow("Skip go_home — immediate stop"))
        return
    mcfg = getattr(app, "_motion_cfg", {}) or {}
    home = np.array(mcfg.get("home", MOTION_HOME), dtype=float)
    logger.info(green(f"Go home → {home}"))
    app.controller.move_to_point(home, speed=speed, acc=acc)
