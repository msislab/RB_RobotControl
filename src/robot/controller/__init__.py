"""Robot controller package."""

from src.robot.controller.base import RobotController
# Import all modules to register their methods
from src.robot.controller import motion, settings, task, script, icv, state

__all__ = ['RobotController']

