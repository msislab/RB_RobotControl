"""Robot connection wrapper - uses ConnectionManager."""

from src.robot.connection.manager import ConnectionManager


class RobotConnection(ConnectionManager):
    """Handles robot connection and initialization - wrapper around ConnectionManager."""
    
    def __init__(self, robot_ip: str):
        """
        Initialize the robot connection.
        
        Args:
            robot_ip: IP address of the robot controller
        """
        super().__init__(robot_ip)

