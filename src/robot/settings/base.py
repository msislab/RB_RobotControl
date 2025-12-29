"""Base robot settings class."""

from typing import Optional
import rbpodo as rb
from loguru import logger


class RobotSettings:
    """Handles robot settings and configuration."""
    
    def __init__(self, robot: Optional[rb.Cobot], rc: Optional[rb.ResponseCollector]):
        """
        Initialize the robot settings handler.
        
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

