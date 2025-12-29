"""Collision detection and control settings."""

import rbpodo as rb
from loguru import logger
from src.utils.color import yellow, green
from src.robot.settings.base import RobotSettings


def set_collision_mode(settings: RobotSettings, mode: int):
    """
    Set collision detection mode.
    
    Args:
        settings: RobotSettings instance
        mode: Collision mode (check rbpodo documentation for valid values)
    """
    settings._check_connection()
    logger.info(yellow(f"       -> Setting collision mode to {mode}"))
    ret = settings.robot.set_collision_mode(settings.rc, mode)
    logger.info(green(f"       -> Collision mode set, return: {ret}"))


def set_collision_onoff(settings: RobotSettings, enable: bool):
    """
    Enable or disable collision detection.
    
    Args:
        settings: RobotSettings instance
        enable: True to enable, False to disable collision detection
    """
    settings._check_connection()
    logger.info(yellow(f"       -> {'Enabling' if enable else 'Disabling'} collision detection"))
    ret = settings.robot.set_collision_onoff(settings.rc, enable)
    status = "enabled" if enable else "disabled"
    logger.info(green(f"       -> Collision detection {status}, return: {ret}"))


def set_collision_threshold(settings: RobotSettings, threshold: float):
    """
    Set collision detection threshold.
    
    Args:
        settings: RobotSettings instance
        threshold: Collision threshold value (check rbpodo documentation for valid range)
    """
    settings._check_connection()
    logger.info(yellow(f"       -> Setting collision threshold to {threshold}"))
    ret = settings.robot.set_collision_threshold(settings.rc, threshold)
    logger.info(green(f"       -> Collision threshold set, return: {ret}"))

