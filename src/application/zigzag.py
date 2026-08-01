"""ZigZag move_speed_l routine with graceful / immediate stop."""

from __future__ import annotations

import time
from typing import Any

import numpy as np
from loguru import logger

from src.application.home import go_home
from src.config.loader import (
    MOTION_ALPHA,
    MOTION_GAIN,
    MOTION_HOME,
    MOTION_OFFSET,
    MOTION_SPEED_BAR,
    MOTION_T1,
    MOTION_T2,
    MOTION_TIME_STEP,
    MOTION_Z,
)
from src.utils.color import green


def _sleep(app: Any, seconds: float) -> None:
    """Sleep in short slices; wake early on either stop flag."""
    end = time.monotonic() + max(0.0, float(seconds))
    while time.monotonic() < end:
        if app.stop_requested or app.immediate_stop:
            return
        time.sleep(min(0.05, end - time.monotonic()))


def execute_zigzag(app: Any) -> None:
    """ZigZag routine — move_speed_l path (params from GUI/config motion)."""
    if not app.running and not app.stop_requested and not app.immediate_stop:
        raise RuntimeError("Application not set up. Call setup() first.")
    if app.stop_requested or app.immediate_stop:
        logger.info(green("ZigZag skipped — stop already requested"))
        if app.stop_requested and not app.immediate_stop:
            go_home(app)
        return
    app.running = True

    mcfg = getattr(app, "_motion_cfg", {}) or {}
    home = np.array(mcfg.get("home", MOTION_HOME), dtype=float)
    time_step = float(mcfg.get("time_step", MOTION_TIME_STEP))
    t1 = float(mcfg.get("t1", MOTION_T1))
    t2 = float(mcfg.get("t2", MOTION_T2))
    gain = float(mcfg.get("gain", MOTION_GAIN))
    alpha = float(mcfg.get("alpha", MOTION_ALPHA))
    z = float(mcfg.get("z", MOTION_Z))
    zeros = np.zeros(6)
    logger.info(green("       -> ZigZag start (speed_bar re-read each outer loop)"))

    for _outer in range(50000):
        if app.stop_requested or app.immediate_stop:
            break
        mcfg = getattr(app, "_motion_cfg", {}) or {}
        speed_bar = float(mcfg.get("speed_bar", MOTION_SPEED_BAR))
        offset = float(mcfg.get("offset", MOTION_OFFSET)) * speed_bar
        motions = [
            [0, offset, offset, 0, 0, 0],
            [offset, offset, 0, 0, 0, 0],
            [offset, 0, -offset, 0, 0, 0],
            [0, -offset, offset, 0, 0, 0],
            [-offset, -offset, 0, 0, 0, 0],
            [-offset, 0, -offset, 0, 0, 0],
        ]
        app.controller.move_speed_l(zeros, t1=t1, t2=t2, gain=gain, alpha=alpha)
        _sleep(app, 0.5)
        if app.stop_requested or app.immediate_stop:
            break

        _x, _y, _z, _rx, _ry, _rz = home
        app.controller.move_to_point(
            np.array([_x, _y, z, _rx, _ry, _rz]), speed=100, acc=500
        )
        if app.stop_requested or app.immediate_stop:
            break
        for _inner in range(20):
            if app.stop_requested or app.immediate_stop:
                break
            for m in motions:
                if app.stop_requested or app.immediate_stop:
                    break
                app.controller.move_speed_l(
                    np.array(m), t1=t1, t2=t2, gain=gain, alpha=alpha
                )
                _sleep(app, time_step)
        if app.stop_requested or app.immediate_stop:
            break
        logger.info(green(
            f"       -> TCP={app.controller.get_tcp_position()} "
            f"speed_bar={speed_bar} offset={offset}"
        ))

    if app.immediate_stop:
        logger.info(green("ZigZag exited (immediate stop)"))
        return

    app.controller.move_speed_l(zeros, t1=t1, t2=t2, gain=gain, alpha=alpha)
    _sleep(app, 0.1)
    if app.stop_requested and not app.immediate_stop:
        go_home(app)
    logger.info(green("ZigZag exited"))
