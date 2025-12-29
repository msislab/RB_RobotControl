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
        
        home = np.array([400.0, 400.0, 400.0, 90.0, 45.0, -130.0])
        
        # Example motion sequence
        logger.info(cyan("Executing motion sequence"))
        target_tcp = home
        self.controller.move_to_point(target_tcp, speed=100, acc=500)

        # Get current joint angles
        logger.info(cyan("Getting current joint angles"))
        current_joints = self.controller.get_joint_angles()

        # Set joint and linear speed


        # Use Jog L to move the robot in a square pattern
        logger.info(cyan("Jogging robot in Cartesian space"))
        # self.controller.jog_robot_l(1, np.array([0, 0, 10, 0, 0, 0]))


        # Use Move Speed L to move the robot in a square pattern
        t = time.time()
        offset = 200
        time_step = 0.3
        t1 = 0.3
        t2 = 0.03
        gain = 0.1
        alpha = 0.05
        # motions = [[x, y, z, 0, 0, 0] for x in (0, offset) for y in (0, offset) for z in (0, offset)]

        z = 400

        for i in range(500):
            # Example motion sequence
            logger.info(cyan("Executing motion sequence"))
            z = 400 + (i%5)*10
            [_x, _y, _z, _rx, _ry, _rz] = home
            target_tcp = np.array([_x, _y, z, _rx, _ry, _rz])
            time.sleep(1)
            self.controller.move_to_point(target_tcp, speed=100, acc=500)
                

            # Define a square motion in x-y axis
            for i in range(2):

                # if self.controller.get_robot_state()[1] == rb.RobotState.Moving:
                #     # Stop Motion
                #     self.controller.jog_robot_l(0, np.array([0, 0, 0, 0, 0, 0]), 5, 5)
                # target_tcp = np.array([400.0, 400.0, 400.0 + i*10, 90.0, 45.0, -130.0])

                # self.controller.move_speed_l(np.array([0, 0, 10, 0, 0, 0]), t1=0.22, t2=0.03, gain=gain, alpha=alpha)
                # time.sleep(0.2)   

                motions = [[0       , offset , 0, 0, 0, 0], 
                           [offset  , offset , 0, 0, 0, 0], 
                           [offset  ,      0 , 0, 0, 0, 0], 
                           [0       , -offset, 0, 0, 0, 0], 
                           [-offset , -offset, 0, 0, 0, 0], 
                           [-offset ,       0, 0, 0, 0, 0]
                           ]
                for m in motions:
                    for i in range(1):
                        # self.controller.jog_robot_l(1, np.array(m), 2, 2)
                        # move_speed_l has built-in collision check that waits for collision to be cleared
                        self.controller.move_speed_l(np.array(m), t1=t1, t2=t2, gain=gain, alpha=alpha)
                        time.sleep(time_step)
            # time.sleep(1)

            current_tcp = self.controller.get_tcp_position()
            logger.info(green(f"       -> Current TCP: {current_tcp}"))
    


        
        # Stop Motion
        self.controller.jog_robot_l(0, np.array([0, 0, 0, 0, 0, 0]), 5, 5)
        time.sleep(0.1)

        # current_tcp = self.controller.get_current_tcp()
        # logger.info(green(f"       -> Current TCP: {current_tcp}"))
        logger.info(cyan("Getting current joint angles"))
        current_joints = self.controller.get_joint_angles()


        # # Example motion sequence
        # logger.info(cyan("Executing motion sequence"))
        # target_tcp = np.array([400.0, 400.0, 400.0, 90.0, 45.0, -130.0])
        # self.controller.move_to_point(target_tcp, speed=100, acc=500)
    
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

