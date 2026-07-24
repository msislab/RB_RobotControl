"""Motion control methods for RobotController."""

import numpy as np
from src.robot.controller.base import RobotController
from src.robot.motion.safety import check_collision_before_motion


def add_motion_methods(cls):
    """Add motion methods to RobotController class."""
    
    def move_to_point(self, point, speed: float = 100, acc: float = 1000):
        """Move robot to point. See RobotMotion.move_to_point() for details."""
        if not check_collision_before_motion(self.connection.data_collector, "move_to_point"):
            return
        self.motion.move_to_point(point, speed, acc)

    def move_j(self, joints: np.ndarray, speed: float = 60, acc: float = 80):
        """Move joints (MoveJ). See RobotMotion.move_j() for details."""
        if not check_collision_before_motion(self.connection.data_collector, "move_j"):
            return
        self.motion.move_j(joints, speed, acc)

    def move_xb(self, steps, **kwargs):
        """MoveXB blended path. See RobotMotion.move_xb()."""
        if not check_collision_before_motion(self.connection.data_collector, "move_xb"):
            return
        self.motion.move_xb(steps, **kwargs)
    
    def move_servo_j(self, joints: np.ndarray, t1: float = 0.002, t2: float = 0.1,
                     gain: float = 1.0, alpha: float = 0.5):
        """Move robot to joint angles using servo control."""
        if not check_collision_before_motion(self.connection.data_collector, "move_servo_j"):
            return
        self.motion.move_servo_j(joints, t1, t2, gain, alpha)
    
    def move_servo_l(self, point: np.ndarray, t1: float = 0.002, t2: float = 0.1,
                     gain: float = 1.0, alpha: float = 0.5):
        """Move robot to Cartesian position using servo control."""
        if not check_collision_before_motion(self.connection.data_collector, "move_servo_l"):
            return
        self.motion.move_servo_l(point, t1, t2, gain, alpha)
    
    def move_speed_j(self, joint_speeds: np.ndarray, t1: float = 0.002, t2: float = 0.1,
                     gain: float = 1.0, alpha: float = 0.5):
        """Move robot with joint angle speed control."""
        if not check_collision_before_motion(self.connection.data_collector, "move_speed_j"):
            return
        self.motion.move_speed_j(joint_speeds, t1, t2, gain, alpha)
    
    def move_speed_l(self, cartesian_speeds: np.ndarray, t1: float = 0.002, t2: float = 0.1,
                     gain: float = 1.0, alpha: float = 0.5):
        """Move robot with Cartesian posture speed control."""
        if not check_collision_before_motion(self.connection.data_collector, "move_speed_l"):
            return
        self.motion.move_speed_l(cartesian_speeds, t1, t2, gain, alpha)
    
    def jog_robot_j(self, mode: int, speeds: np.ndarray,
                    acc_ratio: float = None, dec_ratio: float = None):
        """Jog robot in joint space."""
        # Skip collision check for stop command (mode 0)
        if mode != 0:
            if not check_collision_before_motion(self.connection.data_collector, "jog_robot_j"):
                return
        self.motion.jog_robot_j(mode, speeds, acc_ratio, dec_ratio)
    
    def jog_robot_l(self, mode: int, speeds: np.ndarray,
                    acc_ratio: float = 1.0, dec_ratio: float = 1.0):
        """Jog robot in Cartesian space."""
        # Skip collision check for stop command (mode 0)
        if mode != 0:
            if not check_collision_before_motion(self.connection.data_collector, "jog_robot_l"):
                return
        self.motion.jog_robot_l(mode, speeds, acc_ratio, dec_ratio)
    
    # Attach methods to class
    cls.move_to_point = move_to_point
    cls.move_j = move_j
    cls.move_xb = move_xb
    cls.move_servo_j = move_servo_j
    cls.move_servo_l = move_servo_l
    cls.move_speed_j = move_speed_j
    cls.move_speed_l = move_speed_l
    cls.jog_robot_j = jog_robot_j
    cls.jog_robot_l = jog_robot_l


add_motion_methods(RobotController)

