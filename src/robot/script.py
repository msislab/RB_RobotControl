"""Robot script execution operations."""

import time
from typing import Optional
import rbpodo as rb
from loguru import logger
from src.robot.settings import RobotSettings


class RobotScript:
    """Handles robot script execution."""
    
    def __init__(self, robot: Optional[rb.Cobot], rc: Optional[rb.ResponseCollector]):
        """
        Initialize the robot script handler.
        
        Args:
            robot: Robot Cobot instance
            rc: ResponseCollector instance
        """
        self.robot = robot
        self.rc = rc
        self.settings = RobotSettings(robot, rc)
    
    def _check_connection(self):
        """Check if robot is connected."""
        if self.robot is None or self.rc is None:
            raise RuntimeError("Robot not connected. Call connect() first.")
    
    def send_script(self, cmd: str) -> int:
        """
        Send a single script command to the controller.
        
        Args:
            cmd: Script command string
            
        Returns:
            Return value from the robot
            
        Raises:
            ValueError: If command format is invalid
            RuntimeError: If robot is not connected
        """
        self._check_connection()
        
        cmd = cmd.strip()
        if not cmd.endswith(")"):
            raise ValueError(f"Script command looks wrong: {cmd}")
        
        ret = self.robot.rt_script(self.rc, cmd)
        logger.info("Command Sent: {}, send_script return: {}", cmd, ret)
        return ret
    
    def run_script(self, script: str, enable_rt: bool = True, disable_rt: bool = True):
        """
        Run a script with RT script control.
        
        Args:
            script: Script command to execute
            enable_rt: Whether to enable RT Script before execution
            disable_rt: Whether to disable RT Script after execution
        """
        self._check_connection()
        
        if enable_rt:
            self.settings.rt_script_onoff(True)  # Enable RT Script
        
        self.send_script(script)
        time.sleep(1)
        
        if disable_rt:
            self.settings.rt_script_onoff(False)  # Disable RT Script

