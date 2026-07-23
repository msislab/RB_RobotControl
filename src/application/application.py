"""Main application class that orchestrates robot operations."""

import time
import numpy as np
import rbpodo as rb
from loguru import logger
from src.robot.controller import RobotController
from src.utils.color import *

class RobotApplication:
    """Main application class that orchestrates robot operations."""
    
    def __init__(self, robot_ip: str):
        """
        Initialize the robot application.
        
        Args:
            robot_ip: IP address of the robot controller
        """
        self.robot_ip = robot_ip
        self.controller = RobotController(robot_ip)
        self.running = False
    
    def setup(self):
        """
        Setup robot connection and configuration.
        
        Args:
            operation_mode: Simulation or Real mode
            speed_bar: Speed bar setting (1 = 50%)
        """

        # Connect and initialize robot
        self.controller.connect()
        self.controller.initialize()
        
        self.running = True
        logger.info(green("       -> Robot application setup complete"))
    
    def execute_motion_sequence(self):
        """Execute the main motion sequence."""
        if not self.running:
            raise RuntimeError("Application not set up. Call setup() first.")
        
        home = np.array([-300.0, -450.0, 350.0, 90.0, 0, 0.0])
        
        # # motion sequence
        # logger.info(cyan("Executing motion sequence"))
        # target_tcp = home
        # self.controller.move_to_point(target_tcp, speed=100, acc=500)
        
        # Example: Enable vibrating motion before motion sequence
        # self.controller.enable_vibrating_motion()
        # Or with custom parameters (adjust based on your robot's API):
        # self.controller.set_vibrating_motion(1, 0, 1, 0.8, 20, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

        # Use Move Speed L to move the robot in a square pattern
        t = time.time()
        offset = 600
        
        time_step = 0.1
        t1 = 0.08
        t2 = 0.03
        gain = 0.5
        alpha = 0.05

        z = 350
        
        self.controller
        
        # Repeat the 
        # exit(0)
        for i in range(50000):
            
            # Bring robot to halt.
            self.controller.move_speed_l(np.array([0, 0, 0, 0, 0, 0]), t1=t1, t2=t2, gain=gain, alpha=alpha)
            time.sleep(0.5)
            
            # Move to Home+Z Position
            # z = 400 + (i%5)*10
            [_x, _y, _z, _rx, _ry, _rz] = home
            target_tcp = np.array([_x, _y, z, _rx, _ry, _rz])
            self.controller.move_to_point(target_tcp, speed=100, acc=500)
                                       
            # Define a square motion in x-y axis
            for i in range(20):
                motions = [[0       , offset , offset , 0, 0, 0], 
                           [offset  , offset ,      0 , 0, 0, 0], 
                           [offset  ,      0 ,-offset , 0, 0, 0], 
                           [0       , -offset, offset , 0, 0, 0], 
                           [-offset , -offset,      0 , 0, 0, 0], 
                           [-offset ,       0, -offset, 0, 0, 0]
                           ]
                for m in motions:
                    self.controller.move_speed_l(np.array(m), t1=t1, t2=t2, gain=gain, alpha=alpha)
                    time.sleep(time_step)                

            # Log the current position
            current_tcp = self.controller.get_tcp_position()
            logger.info(green(f"       -> Current TCP: {current_tcp}"))
    
        # Stop Motion
        self.controller.move_speed_l(np.array([0,0,0,0,0,0]), t1=t1, t2=t2, gain=gain, alpha=alpha)
        time.sleep(0.1)
        
        
    
    def execute_icv_sequence(self):
        """
        Execute motion sequence with ICV enabled.
        Put your actual welding / IO logic around this if needed.
        """
        if not self.running:
            raise RuntimeError("Application not set up. Call setup() first.")
        
        # Enable ICV
        self.controller.enable_icv()
        
        # Add your motion commands here while ICV is enabled
        # Example:
        # target_tcp = np.array([500.0, 500.0, 400.0, 90.0, 45.0, -130.0])
        # self.controller.move_to_point(target_tcp, speed=200, acc=2000)
        
        # Disable ICV
        self.controller.disable_icv()
    
    def shutdown(self):
        """Shutdown the application and cleanup resources."""
        self.running = False
        
        # Check for errors
        try:
            self.controller.check_errors()
        except Exception as e:
            logger.error("Error during shutdown: {}", e)
        
        # Stop robot
        self.controller.stop()

        
        logger.info(red(""))
        logger.info(red("Robot application shutdown complete"))

