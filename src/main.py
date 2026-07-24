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
    ROBOT_ENABLED,
    ROBOT_ROUTINE,
    ROBOT_SEQUENCE,
    ROBOT_SEQUENCE_LOOP,
    ROBOT_SEQUENCE_MERGE,
    DEFAULT_OPERATION_MODE,
    JOINT_SPEED,
    JOINT_ACCELERATION,
    CARTESIAN_LINEAR_SPEED,
    CARTESIAN_LINEAR_ACCELERATION,
    SPEED_MULTIPLIER,
    ACCELERATION_MULTIPLIER,
    LOGGER_LEVEL,
    LOGGER_FORMAT,
    LOGGER_COLORIZE,
    CAMERA_ENABLED,
    CAMERA_VIEW,
    CAMERA_FPS,
    CAMERA_SERIAL,
    CAMERA_WIDTH,
    CAMERA_HEIGHT,
    CAMERA_EXPOSURE,
    CAMERA_GAIN,
    STEREO_ENABLED,
    STEREO_BACKEND,
    STEREO_VARIANT,
    STEREO_VALID_ITERS,
    STEREO_Z_FAR,
    STEREO_ONNX_SIZE,
    OMRON_ENABLED,
    OMRON_EXPOSURE,
    OMRON_GAIN,
    OMRON_IP_POOL_CIDR,
    OMRON_PREFERRED_IPS,
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
    from src.camera.omron_camera import (
        get_omron_gain_limits,
        open_omron_devices_at_startup,
        prepare_omron_network,
    )

    display = ensure_display()
    logger.info(cyan(f"Starting Tk GUI on DISPLAY={display}"))
    om_gain_min, om_gain_max = 0.0, 208.0
    if OMRON_ENABLED:
        try:
            prepare_omron_network(OMRON_IP_POOL_CIDR, OMRON_PREFERRED_IPS)
            open_omron_devices_at_startup(
                exposure=OMRON_EXPOSURE, gain=OMRON_GAIN
            )
            om_gain_min, om_gain_max = get_omron_gain_limits()
        except Exception as e:
            logger.warning(yellow(f"Omron startup (IP/open) skipped/failed: {e}"))
    else:
        logger.info("Omron disabled in config — skip IP assign / device open at startup")
    app = RobotApplication(ROBOT_IP)
    defaults = {
        "robot_enabled": ROBOT_ENABLED,
        "robot_routine": ROBOT_ROUTINE,
        "robot_sequence": ROBOT_SEQUENCE,
        "robot_sequence_loop": ROBOT_SEQUENCE_LOOP,
        "robot_sequence_merge": ROBOT_SEQUENCE_MERGE,
        "robot_ip": ROBOT_IP,
        "operation_mode": DEFAULT_OPERATION_MODE,
        "joint_speed": JOINT_SPEED,
        "joint_acc": JOINT_ACCELERATION,
        "linear_speed": CARTESIAN_LINEAR_SPEED,
        "linear_acc": CARTESIAN_LINEAR_ACCELERATION,
        "speed_multiplier": SPEED_MULTIPLIER,
        "acceleration_multiplier": ACCELERATION_MULTIPLIER,
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
        "camera_exposure": CAMERA_EXPOSURE,
        "camera_gain": CAMERA_GAIN,
        "stereo_enabled": STEREO_ENABLED,
        "stereo_backend": STEREO_BACKEND,
        "stereo_variant": STEREO_VARIANT,
        "stereo_valid_iters": STEREO_VALID_ITERS,
        "stereo_z_far": STEREO_Z_FAR,
        "stereo_onnx_size": STEREO_ONNX_SIZE,
        "omron_enabled": OMRON_ENABLED,
        "omron_exposure": OMRON_EXPOSURE,
        "omron_gain": OMRON_GAIN,
        "omron_gain_min": om_gain_min,
        "omron_gain_max": om_gain_max,
        "omron_ip_pool_cidr": OMRON_IP_POOL_CIDR,
        "omron_preferred_ips": OMRON_PREFERRED_IPS,
    }
    CameraControlGui(app, defaults=defaults).run()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception("Error in main execution: {}", e)
