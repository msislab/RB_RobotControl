"""Connection manager for robot connections."""

from typing import Optional
import rbpodo as rb
from loguru import logger
from src.config.loader import load_config
from src.robot.data.collector import DataCollector
from src.robot.settings import RobotSettings
from src.utils.color import yellow, green, orange


class ConnectionManager:
    """Manages robot connection and initialization."""
    
    def __init__(self, robot_ip: str):
        """
        Initialize the connection manager.
        
        Args:
            robot_ip: IP address of the robot controller
        """
        self.robot_ip = robot_ip
        self.robot: Optional[rb.Cobot] = None
        self.rc: Optional[rb.ResponseCollector] = None
        self.data_collector = DataCollector(self.robot_ip)
        self.settings: Optional[RobotSettings] = None
        self.config = load_config()
    
    def connect(self):
        """Establish connection to the robot and initialize."""
        self.robot = rb.Cobot(self.robot_ip)
        self.data_collector.start()
        self.rc = rb.ResponseCollector()
        self.robot.flush(self.rc)
        self.settings = RobotSettings(self.robot, self.rc)
        logger.info(green("       -> Robot connection established"))
    
    def initialize(self):
        """
        Initialize robot settings.
        
        Args:
            operation_mode: Simulation or Real mode
            speed_bar: Speed bar setting (1 = 50%)
            enable_waiting_ack: Whether to enable waiting for acknowledgment
        """
        if self.robot is None or self.rc is None:
            raise RuntimeError("Robot not connected. Call connect() first.")
        
        self.settings.rt_script_onoff(False)  # Disable RT Script
        self.settings.task_stop()

        enable_waiting_ack = self.config['enable_waiting_ack']
        
        operation_mode = self.config['default_operation_mode']
        speed_bar = self.config['default_speed_bar']
        speed_multiplier = self.config['speed']['speed_multiplier']
        acc_multiplier = self.config['speed']['acceleration_multiplier']
        speed_j = self.config['speed']['joint']['speed']
        acceleration_j = self.config['speed']['joint']['acceleration']
        speed_l = self.config['speed']['cartesian']['linear_speed']
        acceleration_l = self.config['speed']['cartesian']['linear_acceleration']
        
        if enable_waiting_ack:
            self.settings.enable_waiting_ack()
        else:
            self.settings.disable_waiting_ack()
        
        self.settings.set_operation_mode(operation_mode)
        self.settings.set_speed_bar(speed_bar)
        self.settings.set_speed_multiplier(speed_multiplier)
        self.settings.set_acc_multiplier(acc_multiplier)

        self.settings.set_speed_acc_j(speed_j, acceleration_j)
        self.settings.set_speed_acc_l(speed_l, acceleration_l)
        
        # Apply collision detection settings
        collision_config = self.config.get('collision_detection', {})
        collision_mode = collision_config.get('mode', 1)
        collision_threshold = collision_config.get('threshold', 0.2)
        
        if collision_mode == 0:
            # Mode 0: Disable collision detection
            self.settings.set_collision_onoff(False)
        elif collision_mode == 1:
            # Mode 1: Enable collision detection with threshold
            self.settings.set_collision_onoff(True)
            self.settings.set_collision_threshold(collision_threshold)
        else:
            logger.warning(f"Unknown collision mode: {collision_mode}, defaulting to mode 1")
            self.settings.set_collision_onoff(True)
            self.settings.set_collision_threshold(collision_threshold)
        
        # # Set collision mode
        # self.settings.set_collision_mode(collision_mode)



    
    def check_errors(self):
        """Check for errors and raise exception if any exist."""
        if self.rc is None:
            raise RuntimeError("Robot not connected. Call connect() first.")
        
        self.rc.error().throw_if_not_empty()
    
    def stop(self):
        """Stop robot tasks and cleanup."""
        logger.info(orange("Stopping robot"))
        if self.robot is not None and self.rc is not None:
            self.settings.task_stop()
            logger.info(green("       -> Robot stopped"))
        if self.data_collector is not None:
            self.data_collector.stop()
            logger.info(green("       -> Data collector stopped"))

