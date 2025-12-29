"""Base robot controller - initialization and connection."""

from src.robot.connection import RobotConnection
from src.robot.script import RobotScript
from src.robot.motion import RobotMotion
from src.robot.icv import RobotICV
from src.robot.settings import RobotSettings


class RobotController:
    """Main controller class for robot operations."""
    
    def __init__(self, robot_ip: str):
        """
        Initialize the robot controller.
        
        Args:
            robot_ip: IP address of the robot controller
        """
        self.connection = RobotConnection(robot_ip)
        self.script: RobotScript = None
        self.motion: RobotMotion = None
        self.icv: RobotICV = None
        self.settings: RobotSettings = None
    
    def connect(self):
        """Establish connection to the robot and initialize."""
        self.connection.connect()
        self.script = RobotScript(self.connection.robot, self.connection.rc)
        self.motion = RobotMotion(self.connection.robot, self.connection.rc)
        self.icv = RobotICV(self.script)
        self.settings = RobotSettings(self.connection.robot, self.connection.rc)
    
    def initialize(self):
        """Initialize robot settings. See RobotConnection.initialize() for details."""
        self.connection.initialize()
    
    def check_errors(self):
        """Check for errors. See RobotConnection.check_errors() for details."""
        self.connection.check_errors()
    
    def stop(self):
        """Stop robot tasks. See RobotConnection.stop() for details."""
        self.connection.stop()

