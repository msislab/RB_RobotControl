"""Acceleration-related settings functions."""

from loguru import logger
from src.utils.color import yellow, green
from src.robot.settings.base import RobotSettings


def set_acc_multiplier(settings: RobotSettings, multiplier: float):
    """
    Set overall acceleration multiplier on the robot (0~2, default 1.0).
    
    Args:
        settings: RobotSettings instance
        multiplier: Acceleration multiplier value
    """
    settings._check_connection()
    m = max(0.0, min(2.0, float(multiplier)))
    logger.info(yellow(f"       -> Setting acceleration multiplier to {m}"))
    ret = settings.robot.set_acc_multiplier(settings.rc, m)
    logger.info(green(f"       -> Acceleration multiplier set to {m}, return: {ret}"))


def set_speed_acc_j(settings: RobotSettings, speed: float, acceleration: float):
    """
    Set fixed joint velocity/acceleration for J-series motions (MoveJ, MoveJB, MoveJL).
    
    Args:
        settings: RobotSettings instance
        speed: Speed/velocity in deg/s (does not use negative value)
        acceleration: Acceleration in deg/s² (does not use negative value)
    """
    settings._check_connection()
    if speed < 0:
        raise ValueError("speed must be non-negative, got {speed}")
    if acceleration < 0:
        raise ValueError("acceleration must be non-negative, got {acceleration}")
    
    logger.info(yellow(f"       -> Setting joint speed/acceleration: speed={speed} deg/s, accel={acceleration} deg/s²"))
    ret = settings.robot.set_speed_acc_j(settings.rc, speed, acceleration)
    logger.info(green(f"       -> Joint speed/acceleration set, return: {ret}"))


def set_speed_acc_l(settings: RobotSettings, speed: float, acceleration: float):
    """
    Set fixed linear velocity/acceleration for L-series motions (MoveL, MovePB, MoveLB, MoveITPL).
    
    Args:
        settings: RobotSettings instance
        speed: Speed/velocity in mm/s
        acceleration: Acceleration in mm/s²
    """
    settings._check_connection()
    if speed < 0:
        raise ValueError("speed must be non-negative, got {speed}")
    if acceleration < 0:
        raise ValueError("acceleration must be non-negative, got {acceleration}")
    
    logger.info(yellow(f"       -> Setting Cartesian speed/acceleration: speed={speed} mm/s, accel={acceleration} mm/s²"))
    ret = settings.robot.set_speed_acc_l(settings.rc, speed, acceleration)
    logger.info(green(f"       -> Cartesian speed/acceleration set, return: {ret}"))

