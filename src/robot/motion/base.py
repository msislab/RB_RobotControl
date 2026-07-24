"""Base robot motion operations."""

from typing import Optional
import numpy as np
import rbpodo as rb
from loguru import logger
from src.utils.color import yellow, green
from src.robot.motion.servo import move_servo_j, move_servo_l
from src.robot.motion.speed import move_speed_j, move_speed_l
from src.robot.motion.jog import jog_robot_j, jog_robot_l
from src.robot.motion.wait import wait_move_done
from src.robot.motion.xb import run_move_xb


class RobotMotion:
    """Handles robot motion and state queries."""
    
    def __init__(self, robot: Optional[rb.Cobot], rc: Optional[rb.ResponseCollector]):
        """
        Initialize the robot motion handler.
        
        Args:
            robot: Robot Cobot instance
            rc: ResponseCollector instance
        """
        self.robot = robot
        self.rc = rc
    
    def _check_connection(self):
        """Check if robot is connected."""
        if self.robot is None or self.rc is None:
            raise RuntimeError("Robot not connected. Call connect() first.")

    def move_to_point(self, point: np.ndarray, speed: float = 100, acc: float = 1000):
        """
        Move robot to specified point and wait for completion.
        
        Args:
            point: Target TCP position [x, y, z, rx, ry, rz]
            speed: Movement speed
            acc: Movement acceleration
        """
        self._check_connection()

        logger.info(yellow(f"       Moving robot to point: {point}"))
        ret = self.robot.move_l(self.rc, point, speed, acc, return_on_err=False)
        logger.info(yellow(f"       -> move_l return: {ret}"))
        wait_move_done(self.robot, self.rc)
        logger.info(green(f"       -> Robot moved to point: {point}"))

    def move_j(self, joints: np.ndarray, speed: float = 60, acc: float = 80):
        """Move joints with MoveJ and wait for completion."""
        self._check_connection()
        logger.info(yellow(f"       Moving robot joints: {joints}"))
        ret = self.robot.move_j(self.rc, joints, speed, acc, return_on_err=False)
        logger.info(yellow(f"       -> move_j return: {ret}"))
        wait_move_done(self.robot, self.rc)
        logger.info(green(f"       -> Robot moved joints: {joints}"))

    def move_xb(self, steps, **kwargs) -> None:
        """Blended MoveXB path (mixed TCP/joint). See run_move_xb()."""
        run_move_xb(self, steps, **kwargs)
    
    def move_servo_j(self, joints: np.ndarray, t1: float = 0.002, t2: float = 0.1,
                     gain: float = 1.0, alpha: float = 0.5):
        """Move robot to joint angles using servo control."""
        move_servo_j(self, joints, t1, t2, gain, alpha)
    
    def move_servo_l(self, point: np.ndarray, t1: float = 0.002, t2: float = 0.1,
                     gain: float = 1.0, alpha: float = 0.5):
        """Move robot to Cartesian position using servo control."""
        move_servo_l(self, point, t1, t2, gain, alpha)
    
    def move_speed_j(self, joint_speeds: np.ndarray, t1: float = 0.002, t2: float = 0.1,
                     gain: float = 1.0, alpha: float = 0.5):
        """Move robot with joint angle speed control."""
        move_speed_j(self, joint_speeds, t1, t2, gain, alpha)
    
    def move_speed_l(self, cartesian_speeds: np.ndarray, t1: float = 0.002, t2: float = 0.1,
                     gain: float = 1.0, alpha: float = 0.5):
        """Move robot with Cartesian posture speed control."""
        move_speed_l(self, cartesian_speeds, t1, t2, gain, alpha)
    
    def jog_robot_j(self, mode: int, speeds: np.ndarray,
                    acc_ratio: float = 1.0, dec_ratio: float = 1.0):
        """Jog robot in joint space. Mode: 0=Stop, 1=Robot Arm, 2=Auxiliary."""
        jog_robot_j(self, mode, speeds, acc_ratio, dec_ratio)
    
    def jog_robot_l(self, mode: int, speeds: np.ndarray,
                    acc_ratio: float = 1.0, dec_ratio: float = 1.0):
        """Jog robot in Cartesian space. Mode: 0=Stop, 1=Global, 2=Tool, 3~5=User."""
        jog_robot_l(self, mode, speeds, acc_ratio, dec_ratio)
    
    def get_joint_angles(self) -> np.ndarray:
        """Get current joint angles."""
        self._check_connection()
        return self.robot.get_joint_angles(self.rc)
    
    def get_robot_state(self) -> tuple:
        """Get current robot state."""
        self._check_connection()
        return self.robot.get_robot_state(self.rc)

    def get_tcp_position(self) -> np.ndarray:
        """Get current TCP pose."""
        self._check_connection()
        return self.robot.get_tcp_position(self.rc)

