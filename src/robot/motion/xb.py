"""MoveXB: clear → add mixed TCP/joint points → run (blended path)."""

from __future__ import annotations

from typing import List, Sequence, Tuple

import numpy as np
import rbpodo as rb
from loguru import logger

from src.robot.motion.wait import wait_move_done
from src.utils.color import green, yellow

Step = Tuple[str, np.ndarray]  # mode tcp|joint, pose[6]


def run_move_xb(
    motion,
    steps: Sequence[Step],
    *,
    linear_speed: float = 100.0,
    linear_acc: float = 500.0,
    joint_speed: float = 60.0,
    joint_acc: float = 80.0,
    blend_distance: float = 100.0,
) -> None:
    """
    Pack sequence into one MoveXB (same pattern as AIRobot_Framework).

    Intermediate points use distance blend; last point blend=0.
    Requires rbpodo >= 0.16.10 (move_xb_*).
    """
    motion._check_connection()
    if not steps:
        logger.warning(yellow("MoveXB: empty steps"))
        return
    if not hasattr(motion.robot, "move_xb_clear"):
        raise RuntimeError(
            "rbpodo missing MoveXB — upgrade: pip install 'rbpodo>=0.16.14'"
        )

    robot, rc = motion.robot, motion.rc
    logger.info(green(f"MoveXB: {len(steps)} point(s)"))
    robot.move_xb_clear(rc, return_on_error=False)
    n = len(steps)
    for i, (mode, pose) in enumerate(steps):
        arr = np.asarray(pose, dtype=float).reshape(6)
        blend = 0.0 if i == n - 1 else float(blend_distance)
        if mode == "joint":
            robot.move_xb_j_add(
                rc, arr, float(joint_speed), float(joint_acc),
                rb.BlendingOption.Distance, blend, return_on_error=False,
            )
            logger.info(yellow(f"       xb_j_add [{i+1}/{n}] blend={blend}"))
        else:
            robot.move_xb_p_add(
                rc, arr, float(linear_speed), float(linear_acc),
                rb.BlendingOption.Distance, blend, return_on_error=False,
            )
            logger.info(yellow(f"       xb_p_add [{i+1}/{n}] blend={blend}"))

    ret = robot.move_xb_run(rc, rb.MoveXBOption.Position, return_on_error=False)
    logger.info(yellow(f"       -> move_xb_run: {ret}"))
    wait_move_done(robot, rc)
    logger.info(green("MoveXB finished"))
