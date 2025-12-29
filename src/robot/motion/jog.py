"""Jog motion control functions."""

import numpy as np
from loguru import logger
from src.utils.color import yellow, green


def _validate_acc_dec_ratio(acc_ratio: float = 1.0, dec_ratio: float = 1.0):
    """Validate acceleration/deceleration ratio parameters."""
    if not (0.0 <= acc_ratio <= 10.0):
        raise ValueError(f"acc_ratio must be between 0.0 and 10.0, got {acc_ratio}")
    if not (0.0 <= dec_ratio <= 10.0):
        raise ValueError(f"dec_ratio must be between 0.0 and 10.0, got {dec_ratio}")


def _build_jog_cmd(func_name: str, mode: int, speeds: np.ndarray,
                   acc_ratio: float = 1.0, dec_ratio: float = 1.0) -> str:
    """Build jog command string."""
    speeds_str = ",".join([f"{int(s)}" for s in speeds])
    return f"{func_name}({mode},{speeds_str},{acc_ratio:.2f},{dec_ratio:.2f})"


def _execute_jog_cmd(motion, cmd: str, mode_name: str, speeds: np.ndarray,
                     acc_ratio: float = 1.0, dec_ratio: float = 1.0) -> int:
    """Execute jog command and log result."""
    has_ratios = acc_ratio is not None and dec_ratio is not None
    if has_ratios:
        logger.info(yellow(f"       Jogging robot - Mode: {mode_name}, "
                          f"Speeds: {speeds}, Acc: {acc_ratio}, Dec: {dec_ratio}"))
    else:
        logger.info(yellow(f"       Jogging robot - Mode: {mode_name}, Speeds: {speeds}"))
    
    logger.info(yellow(f"       -> Sending command: {cmd}"))
    from src.robot.settings import RobotSettings
    settings = RobotSettings(motion.robot, motion.rc)
    settings.rt_script_onoff(True)
    ret = motion.robot.rt_script(motion.rc, cmd)
    settings.rt_script_onoff(False)
    logger.info(green(f"           <- Command return: {ret}"))
    return ret


def jog_robot_j(motion, mode: int, speeds: np.ndarray, 
                acc_ratio: float = 1.0, dec_ratio: float = 1.0):
    """
    Jog robot in joint space.
    
    Args:
        motion: RobotMotion instance
        mode: 0=Stop, 1=Robot Arm Joint, 2=Auxiliary Axis
        speeds: Joint speeds [speed0~5] in deg/s
        acc_ratio: Acceleration ratio (0.0~10.0, default: 1.0)
        dec_ratio: Deceleration ratio (0.0~10.0, default: 1.0)
    """
    motion._check_connection()
    
    if mode not in [0, 1, 2]:
        raise ValueError(f"mode must be 0, 1, or 2, got {mode}")
    if len(speeds) != 6:
        raise ValueError(f"speeds must have 6 elements, got {len(speeds)}")
    
    _validate_acc_dec_ratio(acc_ratio, dec_ratio)
    
    mode_names = {0: "Stop", 1: "Robot Arm Joint", 2: "Auxiliary Axis"}
    cmd = _build_jog_cmd("jog_robot_j", mode, speeds, acc_ratio, dec_ratio)
    _execute_jog_cmd(motion, cmd, mode_names[mode], speeds, acc_ratio, dec_ratio)


def jog_robot_l(motion, mode: int, speeds: np.ndarray,
                acc_ratio: float = 1.0, dec_ratio: float = 1.0):
    """
    Jog robot in Cartesian space.
    
    Args:
        motion: RobotMotion instance
        mode: 0=Stop, 1=Global, 2=Tool, 3~5=User 0~2
        speeds: [x, y, z, rx, ry, rz] - xyz in mm/s (-250~250), rxyz in deg/s (-45~45)
        acc_ratio: Acceleration ratio (0.0~10.0, default: 1.0)
        dec_ratio: Deceleration ratio (0.0~10.0, default: 1.0)
    """
    motion._check_connection()
    
    if mode not in [0, 1, 2, 3, 4, 5]:
        raise ValueError(f"mode must be 0~5, got {mode}")
    if len(speeds) != 6:
        raise ValueError(f"speeds must have 6 elements, got {len(speeds)}")
    if np.any(np.abs(speeds[:3]) > 250):
        raise ValueError(f"x, y, z speeds must be in [-250, 250] mm/s, got {speeds[:3]}")
    if np.any(np.abs(speeds[3:]) > 45):
        raise ValueError(f"rx, ry, rz speeds must be in [-45, 45] deg/s, got {speeds[3:]}")
    
    _validate_acc_dec_ratio(acc_ratio, dec_ratio)
    
    mode_names = {0: "Stop", 1: "Global", 2: "Tool", 3: "User 0", 4: "User 1", 5: "User 2"}
    cmd = _build_jog_cmd("jog_robot_l", mode, speeds, acc_ratio, dec_ratio)
    _execute_jog_cmd(motion, cmd, mode_names[mode], speeds, acc_ratio, dec_ratio)

