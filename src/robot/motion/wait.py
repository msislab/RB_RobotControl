"""Block until move_l / move_j motion finishes."""

from __future__ import annotations

import time
from typing import Any, Callable, Optional

import rbpodo as rb
from loguru import logger

from src.utils.color import yellow

AbortCheck = Optional[Callable[[], bool]]


def wait_move_done(
    robot: Any,
    rc: Any,
    timeout: float = -1.0,
    abort_check: AbortCheck = None,
) -> None:
    """
    Wait for the last MoveJ/MoveL/MoveXB to finish.

    Use wait_for_move_started, then RobotState polling for finished.
    A long wait_for_move_finished holds the Cobot command channel and
    blocks live set_speed_bar (and other settings) until the move ends.

    ``abort_check`` (e.g. immediate stop) returns early without waiting
    for idle — pair with ``task_stop()`` from the GUI thread.
    """
    if abort_check and abort_check():
        logger.info(yellow("       -> wait_move_done aborted before start"))
        return
    start_t = time.monotonic()
    start_timeout = 5.0 if timeout < 0 else min(float(timeout), 5.0)
    # Slice start-wait so Immediate Stop can cut in (task_stop may end the move).
    deadline = start_t + start_timeout
    started = None
    while True:
        if abort_check and abort_check():
            logger.info(yellow("       -> wait_move_done aborted during start-wait"))
            return
        slice_t = min(0.2, max(0.05, deadline - time.monotonic()))
        if slice_t <= 0:
            break
        started = robot.wait_for_move_started(
            rc, timeout=slice_t, return_on_error=False
        )
        if _ret_type(started) == rb.ReturnType.Success:
            break
        if time.monotonic() >= deadline:
            break
    stype = _ret_type(started)
    logger.info(yellow(f"       -> wait_for_move_started: {started} ({stype})"))
    if stype != rb.ReturnType.Success:
        logger.warning(yellow("wait_for_move_started failed — polling RobotState"))

    _poll_until_idle(robot, rc, start_t, timeout, abort_check)


def _ret_type(ret: Any):
    try:
        return ret.type()
    except Exception:
        return None


def _poll_until_idle(
    robot: Any,
    rc: Any,
    start_t: float,
    timeout: float,
    abort_check: AbortCheck = None,
) -> None:
    saw_moving = False
    idle_ok = 0
    while True:
        if abort_check and abort_check():
            logger.info(yellow("       -> wait_move_done aborted while polling"))
            return
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
