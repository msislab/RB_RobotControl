"""Operation mode and control settings."""

import rbpodo as rb
from loguru import logger
from src.utils.color import yellow, green
from src.robot.settings.base import RobotSettings


def set_operation_mode(settings: RobotSettings, operation_mode):
    """
    Set robot operation mode.
    
    Args:
        settings: RobotSettings instance
        operation_mode: Simulation or Real mode (rb.OperationMode enum or string)
    """
    settings._check_connection()
    
    # Convert string to enum if needed
    if isinstance(operation_mode, str):
        operation_mode = (
            rb.OperationMode.Real if operation_mode.lower() == "real"
            else rb.OperationMode.Simulation
        )
    
    logger.info(yellow(f"       -> Setting operation mode to {operation_mode}"))
    settings.robot.set_operation_mode(settings.rc, operation_mode)
    logger.info(green(f"       -> Operation mode set to {operation_mode}"))


def enable_waiting_ack(settings: RobotSettings):
    """Enable waiting for acknowledgment."""
    settings._check_connection()
    settings.robot.enable_waiting_ack(settings.rc)
    logger.info(green("       -> Waiting acknowledgment enabled"))


def disable_waiting_ack(settings: RobotSettings):
    """Disable waiting for acknowledgment."""
    settings._check_connection()
    settings.robot.disable_waiting_ack(settings.rc)
    logger.info(green("       -> Waiting acknowledgment disabled"))


def rt_script_onoff(settings: RobotSettings, enable: bool):
    """
    Enable or disable RT Script mode.
    
    Args:
        settings: RobotSettings instance
        enable: True to enable, False to disable
    """
    settings._check_connection()
    settings.robot.rt_script_onoff(settings.rc, enable)
    status = "enabled" if enable else "disabled"
    logger.info(green(f"       -> RT Script {status}"))


def task_stop(settings: RobotSettings):
    """Stop robot tasks."""
    settings._check_connection()
    settings.robot.task_stop(settings.rc)
    logger.info(green("       -> Robot tasks stopped"))


def task_load(settings: RobotSettings, task_name: str):
    """Load a task program."""
    settings._check_connection()
    logger.info(yellow(f"       -> Loading task: {task_name}"))
    ret = settings.robot.task_load(settings.rc, task_name)
    logger.info(green(f"       -> Task loaded, return: {ret}"))


def task_pause(settings: RobotSettings):
    """Pause the current task."""
    settings._check_connection()
    logger.info(yellow("       -> Pausing task"))
    ret = settings.robot.task_pause(settings.rc)
    logger.info(green(f"       -> Task paused, return: {ret}"))


def task_play(settings: RobotSettings):
    """Play/start the current task."""
    settings._check_connection()
    logger.info(yellow("       -> Playing task"))
    ret = settings.robot.task_play(settings.rc)
    logger.info(green(f"       -> Task playing, return: {ret}"))


def task_resume(settings: RobotSettings):
    """Resume the paused task."""
    settings._check_connection()
    logger.info(yellow("       -> Resuming task"))
    ret = settings.robot.task_resume(settings.rc)
    logger.info(green(f"       -> Task resumed, return: {ret}"))

