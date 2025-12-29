"""State query methods for RobotController."""

import numpy as np
from loguru import logger
from src.utils.color import green
from src.robot.controller.base import RobotController


def add_state_methods(cls):
    """Add state query methods to RobotController class."""
    
    def get_joint_angles(self):
        """Get current joint angles. See RobotMotion.get_joint_angles() for details."""
        joints = self.connection.data_collector.data.jnt_ref
        _j = np.array(joints, dtype=float)
        _j = np.round(_j, 2)
        logger.info(green(f"       -> Current joint angles: {_j}"))
        return _j
    
    def get_tcp_position(self):
        """Get current TCP (Tool Center Point) pose [x, y, z, rx, ry, rz]."""
        tcp = self.connection.data_collector.data.tcp_pos
        _tcp = np.array(tcp, dtype=float)
        _tcp = np.round(_tcp, 2)
        logger.info(green(f"       -> Current TCP pose: {_tcp}"))
        return _tcp
    
    def get_robot_state(self):
        """Get current robot state. See RobotMotion.get_robot_state() for details."""
        return self.motion.get_robot_state()
    
    def has_external_collision(self):
        """
        Check if external collision is detected using rbpodo library data.
        
        Returns:
            bool: True if external collision is detected, False otherwise
            
        Note:
            This method checks the op_stat_collision_occur flag from the robot's
            operational status data, which specifically indicates external
            collision detection.
        """
        try:
            # Check if data collector is running and has data
            if not hasattr(self.connection.data_collector, 'data') or \
               self.connection.data_collector.data is None:
                return False
            
            # op_stat_collision_occur: 0 = no external collision, 1 = external collision detected
            collision_detected = self.connection.data_collector.data.op_stat_collision_occur == 1
            
            return collision_detected
        except AttributeError:
            # If data properties don't exist, return False
            logger.warning("Collision detection data not available")
            return False
        except Exception as e:
            logger.error(f"Error checking external collision: {e}")
            return False
    
    def has_self_collision(self):
        """
        Check if self/virtual collision is detected using rbpodo library data.
        
        Returns:
            bool: True if self-collision is detected, False otherwise
            
        Note:
            This method checks the op_stat_self_collision flag from the robot's
            operational status data, which indicates self-collision or virtual
            collision detection (e.g., robot arm hitting itself).
        """
        try:
            # Check if data collector is running and has data
            if not hasattr(self.connection.data_collector, 'data') or \
               self.connection.data_collector.data is None:
                return False
            
            # op_stat_self_collision: 0 = no self-collision, 1 = self-collision detected
            collision_detected = self.connection.data_collector.data.op_stat_self_collision == 1
            
            return collision_detected
        except AttributeError:
            # If data properties don't exist, return False
            logger.warning("Collision detection data not available")
            return False
        except Exception as e:
            logger.error(f"Error checking self-collision: {e}")
            return False
    
    def has_any_collision(self):
        """
        Check if any type of collision is detected (external or self-collision).
        
        Returns:
            bool: True if any collision is detected, False otherwise
            
        Note:
            This is a combined check that returns True if either external collision
            or self-collision is detected. Use this for general collision detection
            when you don't need to distinguish between collision types.
        """
        try:
            # Check if data collector is running and has data
            if not hasattr(self.connection.data_collector, 'data') or \
               self.connection.data_collector.data is None:
                return False
            
            # Check both collision flags
            external_collision = self.connection.data_collector.data.op_stat_collision_occur == 1
            self_collision = self.connection.data_collector.data.op_stat_self_collision == 1
            
            return external_collision or self_collision
        except AttributeError:
            # If data properties don't exist, return False
            logger.warning("Collision detection data not available")
            return False
        except Exception as e:
            logger.error(f"Error checking collision: {e}")
            return False
    
    # Attach methods to class
    cls.get_joint_angles = get_joint_angles
    cls.get_tcp_position = get_tcp_position
    cls.get_robot_state = get_robot_state
    cls.has_external_collision = has_external_collision
    cls.has_self_collision = has_self_collision
    cls.has_any_collision = has_any_collision


add_state_methods(RobotController)

