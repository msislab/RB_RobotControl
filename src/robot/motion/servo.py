"""Servo motion control functions."""

import numpy as np
from loguru import logger
from src.utils.color import yellow


def _validate_servo_params(t1: float, t2: float, gain: float, alpha: float):
    """Validate servo parameters according to documentation."""
    if t1 < 0.002:
        raise ValueError(f"t1 must be >= 0.002, got {t1}")
    if not (0.02 < t2 < 0.2):
        raise ValueError(f"t2 must be between 0.02 and 0.2, got {t2}")
    if gain <= 0:
        raise ValueError(f"gain must be > 0, got {gain}")
    if not (0 < alpha < 1):
        raise ValueError(f"alpha must be between 0 and 1, got {alpha}")


def move_servo_j(motion, joints: np.ndarray, t1: float = 0.002, t2: float = 0.1, 
                 gain: float = 1.0, alpha: float = 0.5):
    """
    Move robot to joint angles using servo control.
    
    Args:
        motion: RobotMotion instance
        joints: Desired joint angles [j0, j1, j2, j3, j4, j5] in degrees (-360 ~ 360)
        t1: Time to reach target point (t1 >= 0.002) in seconds
        t2: Time to maintain the motion after arrival (0.02 < t2 < 0.2) in seconds
        gain: Velocity tracking rate (gain > 0)
        alpha: Low-pass-filter gain. Smaller value = smoother motion (0 < alpha < 1)
        
    Raises:
        ValueError: If parameters are out of valid range
    """
    motion._check_connection()
    _validate_servo_params(t1, t2, gain, alpha)
    
    if len(joints) != 6:
        raise ValueError(f"joints must have 6 elements, got {len(joints)}")
    if np.any(np.abs(joints) > 360):
        raise ValueError(f"Joint angles must be in range [-360, 360] degrees")
    
    logger.info(yellow(f"       Moving robot to joint angles: {joints}"))
    ret = motion.robot.move_servo_j(motion.rc, joints, t1, t2, gain, alpha)
    logger.info(yellow(f"       -> move_servo_j return: {ret}"))


def move_servo_l(motion, point: np.ndarray, t1: float = 0.002, t2: float = 0.1,
                 gain: float = 1.0, alpha: float = 0.5):
    """
    Move robot to Cartesian position using servo control.
    
    Args:
        motion: RobotMotion instance
        point: Desired Cartesian posture [x, y, z, rx, ry, rz]
               x, y, z in mm, rx, ry, rz in degrees (ZY'X'' Euler)
        t1: Time to reach target point (t1 >= 0.002) in seconds
        t2: Time to maintain the motion after arrival (0.02 < t2 < 0.2) in seconds
        gain: Velocity tracking rate (gain > 0)
        alpha: Low-pass-filter gain. Smaller value = smoother motion (0 < alpha < 1)
        
    Raises:
        ValueError: If parameters are out of valid range
    """
    motion._check_connection()
    _validate_servo_params(t1, t2, gain, alpha)
    
    if len(point) != 6:
        raise ValueError(f"point must have 6 elements [x, y, z, rx, ry, rz], got {len(point)}")
    
    logger.info(yellow(f"       Moving robot to Cartesian point: {point}"))
    ret = motion.robot.move_servo_l(motion.rc, point, t1, t2, gain, alpha)
    logger.info(yellow(f"       -> move_servo_l return: {ret}"))

