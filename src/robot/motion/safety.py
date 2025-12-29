"""Safety checks for robot motion."""

from loguru import logger
from src.utils.color import red, yellow, green


def check_collision_before_motion(data_collector, motion_name: str = "motion"):
    """
    Check for collision before motion and wait for user to clear it.
    
    Args:
        data_collector: DataCollector instance to check collision status
        motion_name: Name of the motion command for logging
        
    Returns:
        bool: True if collision is cleared and motion can proceed, False if aborted by user
    """
    try:
        # Check if data collector is available and has data
        if not hasattr(data_collector, 'data') or data_collector.data is None:
            # If data not available, proceed (assume no collision)
            return True
        
        # Check for any collision
        external_collision = data_collector.data.op_stat_collision_occur == 1
        self_collision = data_collector.data.op_stat_self_collision == 1
        
        if external_collision or self_collision:
            # Collision detected - loop until cleared
            while True:
                logger.warning(red("=" * 60))
                logger.warning(red(f"⚠️  COLLISION DETECTED BEFORE {motion_name.upper()}!"))
                
                if external_collision:
                    logger.warning(red("   External collision detected!"))
                if self_collision:
                    logger.warning(red("   Self-collision detected!"))
                
                logger.warning(yellow("   Please clear the collision and ensure the robot is safe."))
                logger.warning(yellow("   Press Enter to continue once collision is cleared..."))
                logger.warning(red("=" * 60))
                
                # Wait for user to press Enter
                try:
                    input()  # Wait for Enter key
                except (EOFError, KeyboardInterrupt):
                    logger.error(red("   Motion aborted by user"))
                    return False
                
                # Re-check collision after user input
                if hasattr(data_collector, 'data') and data_collector.data is not None:
                    external_collision = data_collector.data.op_stat_collision_occur == 1
                    self_collision = data_collector.data.op_stat_self_collision == 1
                    
                    if external_collision or self_collision:
                        logger.error(red("   Collision still detected! Please clear the collision and try again."))
                        logger.warning(yellow("   Waiting for collision to be cleared..."))
                        # Continue loop to ask again
                    else:
                        logger.info(green("   ✓ Collision cleared. Proceeding with motion."))
                        return True
                else:
                    logger.warning(yellow("   Data collector not available. Proceeding with caution."))
                    return True
        
        # No collision detected
        return True
        
    except Exception as e:
        logger.error(f"Error checking collision: {e}")
        logger.warning(yellow("   Proceeding with motion (collision check failed)"))
        return True

