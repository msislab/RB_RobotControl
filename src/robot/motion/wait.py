"""Block until move_l / move_j motion finishes."""

from __future__ import annotations

import time
from typing import Any

import rbpodo as rb
from loguru import logger

from src.utils.color import yellow


def wait_move_done(robot: Any, rc: Any, timeout: float = -1.0) -> None:
    """
    Wait for the last MoveJ/MoveL/MoveXB to finish.

    Use wait_for_move_started, then RobotState polling for finished.
    A long wait_for_move_finished holds the Cobot command channel and
    blocks live set_speed_bar (and other settings) until the move ends.
    """
    start_t = time.monotonic()
    start_timeout = 5.0 if timeout < 0 else min(float(timeout), 5.0)
    started = robot.wait_for_move_started(
        rc, timeout=start_timeout, return_on_error=False
    )
    stype = _ret_type(started)
    logger.info(yellow(f"       -> wait_for_move_started: {started} ({stype})"))
    if stype != rb.ReturnType.Success:
        logger.warning(yellow("wait_for_move_started failed — polling RobotState"))

    _poll_until_idle(robot, rc, start_t, timeout)


def _ret_type(ret: Any):
    try:
        return ret.type()
    except Exception:
        return None


def _poll_until_idle(robot: Any, rc: Any, start_t: float, timeout: float) -> None:
    saw_moving = False
    idle_ok = 0
    while True:
        elapsed = time.monotonic() - start_t
        if timeout >= 0 and elapsed > timeout:
            logger.warning(yellow(f"move wait timed out after {elapsed:.1f}s"))
            return
        try:
            state = robot.get_robot_state(rc)[1]
        except Exception:
            time.sleep(0.02)
            continue
        if state == rb.RobotState.Moving:
            saw_moving = True
            idle_ok = 0
        elif saw_moving:
            idle_ok += 1
            if idle_ok >= 3:
                return
        elif elapsed >= 2.0:
            # Never saw Moving — likely already at target / no motion
            return
        time.sleep(0.02)
