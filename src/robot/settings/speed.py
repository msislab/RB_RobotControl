"""Speed-related settings functions."""

from loguru import logger
from src.utils.color import yellow, green
from src.robot.settings.base import RobotSettings


def set_speed_bar(settings: RobotSettings, speed_bar: int):
    """
    Set robot speed bar.
    
    Args:
        settings: RobotSettings instance
        speed_bar: Speed bar setting (1 = 50%, 2 = 100%, etc.)
    """
    settings._check_connection()
    logger.info(yellow(f"       -> Setting Robot Speed to {speed_bar*100}%"))
    settings.robot.set_speed_bar(settings.rc, speed_bar)
    logger.info(green(f"       -> Robot Speed set to {speed_bar*100}%"))


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

