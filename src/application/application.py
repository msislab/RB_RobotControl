"""Main application class that orchestrates robot operations."""

import threading

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
        self.stop_requested = False
        self.immediate_stop = False
        self._connect_lock = threading.Lock()

    def _wire_abort_check(self) -> None:
        motion = getattr(self.controller, "motion", None)
        if motion is not None:
            motion.abort_check = lambda: bool(self.immediate_stop)

    def request_stop(self) -> None:
        """Graceful stop: finish routine boundary, then go home (no task_stop)."""
        self.stop_requested = True
        self.running = False

    def request_immediate_stop(self) -> None:
        """Hard stop: abort waits and halt robot tasks (keep connection)."""
        self.stop_requested = True
        self.immediate_stop = True
        self.running = False
        if not getattr(self, "_setup_done", False):
            return
        try:
            self.controller.task_stop()
        except Exception as e:
            logger.warning("task_stop on request_immediate_stop failed: {}", e)

    def connect_with_settings(self, cfg: dict) -> None:
        """Connect/reconnect and apply settings; leave motion idle (no routine)."""
        from src.application.connect_cfg import connect_with_settings as _apply

        _apply(self, cfg)
        self._wire_abort_check()

    def clear_stop_flags(self) -> None:
        """Clear stop flags at the start of a new robot worker run."""
        self.stop_requested = False
        self.immediate_stop = False

    def setup_with_settings(self, cfg: dict) -> None:
        """Connect (or reconnect), apply settings, then mark motion running."""
        logger.info(yellow("       -> [robot-cfg] setup_with_settings begin"))
        self.connect_with_settings(cfg)
        # Preserve Stop pressed during connect; only run if not already stopping.
        self.running = not (self.stop_requested or self.immediate_stop)
        logger.info(green("       -> Robot application setup complete"))

    def setup(self):
        """Setup robot connection and configuration (YAML defaults)."""
        self.controller.connect()
        self.controller.initialize()
        self._wire_abort_check()
        self.clear_stop_flags()
        self.running = True
        self._setup_done = True
        logger.info(green("       -> Robot application setup complete"))

    def execute_motion_sequence(self):
        """ZigZag routine — see zigzag.execute_zigzag."""
        from src.application.zigzag import execute_zigzag

        execute_zigzag(self)

    def execute_icv_sequence(self):
        """
        Execute motion sequence with ICV enabled.
        Put your actual welding / IO logic around this if needed.
        """
        if not self.running:
            raise RuntimeError("Application not set up. Call setup() first.")

        self.controller.enable_icv()

        # Add your motion commands here while ICV is enabled
        # Example:
        # target_tcp = np.array([500.0, 500.0, 400.0, 90.0, 45.0, -130.0])
        # self.controller.move_to_point(target_tcp, speed=200, acc=2000)

        self.controller.disable_icv()

    def shutdown(self):
        """Shutdown the application and cleanup resources."""
        self.running = False
        if not getattr(self, "_setup_done", False):
            logger.info(red("Robot was not connected — skip controller shutdown"))
            return
        try:
            self.controller.check_errors()
        except Exception as e:
            logger.error("Error during shutdown: {}", e)
        try:
            self.controller.stop()
        except Exception as e:
            logger.error("Stop during shutdown: {}", e)
        logger.info(red("Robot application shutdown complete"))
