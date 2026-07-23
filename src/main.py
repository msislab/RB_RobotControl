"""Main entry point for the robot application."""

from loguru import logger

from src.utils.logger_config import (
    setup_logger,
    set_simple_format,
    set_detailed_format,
    set_minimal_format,
)
from src.config.loader import (
    ROBOT_IP,
    DEFAULT_OPERATION_MODE,
    JOINT_SPEED,
    JOINT_ACCELERATION,
    CARTESIAN_LINEAR_SPEED,
    CARTESIAN_LINEAR_ACCELERATION,
    LOGGER_LEVEL,
    LOGGER_FORMAT,
    LOGGER_COLORIZE,
    CAMERA_ENABLED,
    CAMERA_VIEW,
    CAMERA_FPS,
    CAMERA_SERIAL,
    CAMERA_WIDTH,
    CAMERA_HEIGHT,
    MOTION_SPEED_BAR,
    MOTION_HOME,
    MOTION_Z,
    MOTION_OFFSET,
    MOTION_TIME_STEP,
    MOTION_T1,
    MOTION_T2,
    MOTION_GAIN,
    MOTION_ALPHA,
)
from src.application.application import RobotApplication
from src.utils.color import *


# Configure logger format based on config
if LOGGER_FORMAT == "simple":
    set_simple_format()
elif LOGGER_FORMAT == "minimal":
    set_minimal_format()
elif LOGGER_FORMAT == "detailed":
    set_detailed_format()
else:
    setup_logger(level=LOGGER_LEVEL, colorize=LOGGER_COLORIZE)


def main():
    """Main entry point — Tk GUI with settings applied on Start."""
    from src.camera.display_env import ensure_display
    from src.camera.display_gui import CameraControlGui

    display = ensure_display()
    logger.info(cyan(f"Starting Tk GUI on DISPLAY={display}"))
    app = RobotApplication(ROBOT_IP)
    defaults = {
        "robot_ip": ROBOT_IP,
        "operation_mode": DEFAULT_OPERATION_MODE,
        "joint_speed": JOINT_SPEED,
        "joint_acc": JOINT_ACCELERATION,
        "linear_speed": CARTESIAN_LINEAR_SPEED,
        "linear_acc": CARTESIAN_LINEAR_ACCELERATION,
        "speed_bar": MOTION_SPEED_BAR,
        "home": MOTION_HOME,
        "z": MOTION_Z,
        "offset": MOTION_OFFSET,
        "time_step": MOTION_TIME_STEP,
        "t1": MOTION_T1,
        "t2": MOTION_T2,
        "gain": MOTION_GAIN,
        "alpha": MOTION_ALPHA,
        "camera_enabled": CAMERA_ENABLED,
        "view": CAMERA_VIEW,
        "fps": CAMERA_FPS,
        "serial": CAMERA_SERIAL,
        "width": CAMERA_WIDTH,
        "height": CAMERA_HEIGHT,
    }
    CameraControlGui(app, defaults=defaults).run()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception("Error in main execution: {}", e)
