"""Vibration-related settings functions."""

from typing import Optional, List, Union
from loguru import logger
from src.utils.color import yellow, green
from src.robot.settings.base import RobotSettings


def set_vibrating_motion(settings: RobotSettings, *args):
    """
    Set vibrating motion parameters.
    
    This function sends the 'set rb_vibrating_motion' command to the robot.
    The exact parameters depend on your robot's firmware/API specification.
    
    Args:
        settings: RobotSettings instance
        *args: Variable arguments for the vibrating motion command.
               Common parameters might include:
               - enable/disable flag
               - intensity/amplitude
               - frequency
               - duration
               - pattern parameters
               
    Examples:
        # Simple enable/disable
        set_vibrating_motion(settings, 1)  # Enable
        set_vibrating_motion(settings, 0)  # Disable
        
        # With parameters (adjust based on your robot's API)
        set_vibrating_motion(settings, 1, 0.8, 20)  # Enable with intensity 0.8, frequency 20
        
        # With full parameter list (as seen in your image)
        set_vibrating_motion(settings, 1, 0, 1, 0.8, 20, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    """
    settings._check_connection()
    
    # Build command string
    if len(args) == 0:
        raise ValueError("set_vibrating_motion requires at least one argument")
    
    # Format arguments as comma-separated string
    args_str = ",".join([str(arg) for arg in args])
    cmd = f"set rb_vibrating_motion({args_str})"
    
    logger.info(yellow(f"       -> Setting vibrating motion with parameters: {args}"))
    
    # Send command using rt_script directly (similar to how jog commands work)
    # Enable RT script mode temporarily
    settings.rt_script_onoff(True)
    ret = settings.robot.rt_script(settings.rc, cmd)
    settings.rt_script_onoff(False)
    
    logger.info(green(f"       -> Vibrating motion set, return: {ret}"))
    return ret


def enable_vibrating_motion(settings: RobotSettings):
    """
    Enable vibrating motion (convenience function).
    
    Args:
        settings: RobotSettings instance
    """
    return set_vibrating_motion(settings, 1)


def disable_vibrating_motion(settings: RobotSettings):
    """
    Disable vibrating motion (convenience function).
    
    Args:
        settings: RobotSettings instance
    """
    return set_vibrating_motion(settings, 0)

