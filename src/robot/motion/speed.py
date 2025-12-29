"""Speed motion control functions."""

import numpy as np
from loguru import logger
from src.utils.color import yellow


def _validate_speed_params(t1: float, t2: float, gain: float, alpha: float):
    """Validate speed parameters according to documentation."""
    if t1 < 0.002:
        raise ValueError(f"t1 must be >= 0.002, got {t1}")
    if not (0.02 < t2 < 0.2):
        raise ValueError(f"t2 must be between 0.02 and 0.2, got {t2}")
    if gain <= 0:
        raise ValueError(f"gain must be > 0, got {gain}")
    if not (0 < alpha < 1):
        raise ValueError(f"alpha must be between 0 and 1, got {alpha}")


def move_speed_j(motion, joint_speeds: np.ndarray, t1: float = 0.002, t2: float = 0.1,
                 gain: float = 1.0, alpha: float = 0.5):
    """
    Move robot with joint angle speed control.
    
    Args:
        motion: RobotMotion instance
        joint_speeds: Desired joint angle speeds [dj0, dj1, dj2, dj3, dj4, dj5] in deg/s
        t1: Arrival time to target point (t1 >= 0.002) in seconds
        t2: Time to maintain the corresponding action after arrival (0.02 < t2 < 0.2) in seconds
        gain: Speed tracking rate (gain > 0), typically gain = 1
        alpha: Low-pass-filter gain. Smaller value = smoother motion (0 < alpha < 1)
        
    Raises:
        ValueError: If parameters are out of valid range
    """
    motion._check_connection()
    _validate_speed_params(t1, t2, gain, alpha)
    
    if len(joint_speeds) != 6:
        raise ValueError(f"joint_speeds must have 6 elements, got {len(joint_speeds)}")
    
    logger.info(yellow(f"       Moving robot with joint speeds: {joint_speeds} deg/s"))
    ret = motion.robot.move_speed_j(motion.rc, joint_speeds, t1, t2, gain, alpha)
    logger.info(yellow(f"       -> move_speed_j return: {ret}"))


def move_speed_l(motion, cartesian_speeds: np.ndarray, t1: float = 0.002, t2: float = 0.1,
                 gain: float = 1.0, alpha: float = 0.5):
    """
    Move robot with Cartesian posture speed control.
    
    Args:
        motion: RobotMotion instance
        cartesian_speeds: Desired Cartesian posture speeds [dx, dy, dz, drx, dry, drz]
                         dx, dy, dz in mm/s, drx, dry, drz in deg/s (ZY'X'' Euler)
        t1: Arrival time to target point (t1 >= 0.002) in seconds
        t2: Time to maintain the corresponding action after arrival (0.02 < t2 < 0.2) in seconds
        gain: Speed tracking rate (gain > 0)
        alpha: Low-pass-filter gain. Smaller value = smoother motion (0 < alpha < 1)
        
    Raises:
        ValueError: If parameters are out of valid range
    """
    motion._check_connection()
    _validate_speed_params(t1, t2, gain, alpha)
    
    if len(cartesian_speeds) != 6:
        raise ValueError(f"cartesian_speeds must have 6 elements [dx, dy, dz, drx, dry, drz], got {len(cartesian_speeds)}")
    
    logger.info(yellow(f"       Moving robot with Cartesian speeds: {cartesian_speeds}"))
    ret = motion.robot.move_speed_l(motion.rc, cartesian_speeds, t1, t2, gain, alpha)
    logger.info(yellow(f"       -> move_speed_l return: {ret}"))

