"""Robot ICV (Imaginary Conveyor) operations."""

import time
from loguru import logger

from src.robot.script import RobotScript
from src.utils.icv_command_builder import ICVCommandBuilder


class RobotICV:
    """Handles robot ICV operations."""
    
    def __init__(self, script_handler: RobotScript):
        """
        Initialize the robot ICV handler.
        
        Args:
            script_handler: RobotScript instance for sending commands
        """
        self.script_handler = script_handler
        self.icv_builder = ICVCommandBuilder()
    
    def enable(self):
        """Enable Imaginary Conveyor mode."""
        self.script_handler.send_script("icv_on()")
        time.sleep(1)
        logger.info("ICV enabled")
    
    def disable(self):
        """Disable Imaginary Conveyor mode."""
        self.script_handler.send_script("icv_off()")
        time.sleep(1)
        logger.info("ICV disabled")
    
    def set(self, t_sec: float, frame: int, x_mm: float, y_mm: float, 
            z_mm: float, rx_deg: float = 0.0, ry_deg: float = 0.0, 
            rz_deg: float = 0.0, mode: int = 0):
        """
        Set ICV parameters.
        
        Args:
            t_sec: Time in seconds
            frame: 0=Global, 1=Tool, 2~4=User coordinates
            x_mm, y_mm, z_mm: Position offsets in mm
            rx_deg, ry_deg, rz_deg: Rotation offsets in degrees
            mode: 0=Relative, 1=Absolute
        """
        cmd = self.icv_builder.build_icv_set_cmd(
            t_sec, frame, x_mm, y_mm, z_mm, rx_deg, ry_deg, rz_deg, mode
        )
        self.script_handler.send_script(cmd)

