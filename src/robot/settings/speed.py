"""Speed-related settings functions."""

from __future__ import annotations

from loguru import logger

from src.robot.settings.base import RobotSettings
from src.utils.color import green, yellow


def set_speed_bar(
    settings: RobotSettings,
    speed_bar: float,
    *,
    timeout: float = -1.0,
) -> None:
    """
    Set robot global speed bar (0~1).

    timeout: rbpodo wait for ACK (-1 = forever). Live GUI updates should pass
    a short timeout so a busy command channel cannot stall the worker thread.
    """
    settings._check_connection()
    sb = max(0.0, min(1.0, float(speed_bar)))
    logger.info(yellow(f"       -> Setting Robot Speed to {sb * 100}%"))
    ret = settings.robot.set_speed_bar(
        settings.rc, sb, timeout=timeout, return_on_error=True
    )
    logger.info(green(f"       -> Robot Speed set to {sb * 100}%, return: {ret}"))


def set_speed_multiplier(settings: RobotSettings, multiplier: float):
    """
    Set overall speed multiplier on the robot (0~2, default 1.0).

    Args:
        settings: RobotSettings instance
        multiplier: Speed multiplier value
    """
    settings._check_connection()
    m = max(0.0, min(2.0, float(multiplier)))
    logger.info(yellow(f"       -> Setting speed multiplier to {m}"))
    ret = settings.robot.set_speed_multiplier(settings.rc, m)
    logger.info(green(f"       -> Speed multiplier set to {m}, return: {ret}"))
