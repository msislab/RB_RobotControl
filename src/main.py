"""Main entry point for the robot application."""

import rbpodo as rb
from loguru import logger

from src.utils.logger_config import setup_logger, set_simple_format, set_detailed_format, set_minimal_format
from src.config.loader import ROBOT_IP, DEFAULT_SPEED_BAR, DEFAULT_OPERATION_MODE, LOGGER_LEVEL, LOGGER_FORMAT, LOGGER_COLORIZE
from src.application.application import RobotApplication
from src.utils.color import *


# Configure logger format based on config
if LOGGER_FORMAT == "simple":
    set_simple_format()
elif LOGGER_FORMAT == "minimal":
    set_minimal_format()
elif LOGGER_FORMAT == "detailed":
    set_detailed_format()
else:
    setup_logger(level=LOGGER_LEVEL, colorize=LOGGER_COLORIZE)


def main():
    """Main entry point for the application."""
    app = RobotApplication(ROBOT_IP)
    
    # Map string config to OperationMode enum
    operation_mode = (
        rb.OperationMode.Real if DEFAULT_OPERATION_MODE.lower() == "real"
        else rb.OperationMode.Simulation
    )
    
    try:
        logger.info(cyan("Starting robot application"))
        # Setup robot using config values
        app.setup()
        
        # Execute motion sequence
        app.execute_motion_sequence()
        
        # Uncomment to execute ICV sequence
        # app.execute_icv_sequence()
        
    except Exception as e:
        logger.error("Error in main execution: {}", e)
        raise
    finally:
        # Always shutdown cleanly
        app.shutdown()


if __name__ == "__main__":
    try: 
        main()
    except Exception as e:
        logger.exception("Error in main execution: {}", e)
        # raise

