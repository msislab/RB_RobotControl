"""Example script demonstrating how to use vibration settings."""

from src.robot.controller import RobotController
from loguru import logger

def main():
    """Example usage of vibration settings."""
    
    # Initialize controller
    robot_ip = "192.168.2.101"  # Update with your robot IP
    controller = RobotController(robot_ip)
    
    try:
        # Connect to robot
        controller.connect()
        controller.initialize()
        
        logger.info("Robot connected and initialized")
        
        # Example 1: Simple enable/disable
        logger.info("Enabling vibrating motion...")
        controller.enable_vibrating_motion()
        
        # Do some operations here...
        
        logger.info("Disabling vibrating motion...")
        controller.disable_vibrating_motion()
        
        # Example 2: Set with custom parameters
        # Adjust parameters based on your robot's API specification
        logger.info("Setting vibrating motion with custom parameters...")
        controller.set_vibrating_motion(1, 0, 1, 0.8, 20, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        # Example 3: Set with minimal parameters (if your robot supports it)
        # controller.set_vibrating_motion(1)  # Enable
        # controller.set_vibrating_motion(0)  # Disable
        
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        controller.stop()
        logger.info("Robot stopped")

if __name__ == "__main__":
    main()

