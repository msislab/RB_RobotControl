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
        self.stop_requested = False

    def request_stop(self) -> None:
        """Ask the motion loop to exit (safe from GUI / other threads)."""
        self.stop_requested = True
        self.running = False

    def setup_with_settings(self, cfg: dict) -> None:
        """Connect (or reconnect) and apply GUI settings, then mark running."""
        ip = (cfg.get("robot_ip") or self.robot_ip).strip()
        need_connect = not getattr(self, "_setup_done", False) or ip != self.robot_ip
        if need_connect:
            if getattr(self, "_setup_done", False):
                try:
                    self.controller.stop()
                except Exception as e:
                    logger.warning("Stop before reconnect: {}", e)
            self.robot_ip = ip
            self.controller = RobotController(ip)
            self.controller.connect()
            self.controller.initialize()
            self._setup_done = True
        else:
            self.running = True

        mode = cfg.get("operation_mode")
        if mode:
            self.controller.settings.set_operation_mode(mode)
        self.controller.set_speed_acc_j(
            float(cfg.get("joint_speed", 180.0)),
            float(cfg.get("joint_acc", 180.0)),
        )
        self.controller.set_speed_acc_l(
            float(cfg.get("linear_speed", 1000.0)),
            float(cfg.get("linear_acc", 1000.0)),
        )
        # Robot API speed bar stays at config default_speed_bar (historically 0.5).
        # GUI motion.speed_bar only scales move_speed_l cartesian speeds.
        from src.config.loader import DEFAULT_SPEED_BAR
        self.controller.set_speed_bar(float(DEFAULT_SPEED_BAR))
        self._motion_cfg = dict(cfg)
        self.running = True
        self.stop_requested = False
        logger.info(green("       -> Robot application setup complete"))

    def setup(self):
        """Setup robot connection and configuration (YAML defaults)."""
        self.controller.connect()
        self.controller.initialize()
        self.running = True
        self.stop_requested = False
        self._setup_done = True
        logger.info(green("       -> Robot application setup complete"))
    
    def execute_motion_sequence(self):
        """Execute the main motion sequence (params from GUI/config motion)."""
        if not self.running and not self.stop_requested:
            raise RuntimeError("Application not set up. Call setup() first.")
        self.running = True
        self.stop_requested = False

        from src.config.loader import (
            MOTION_SPEED_BAR, MOTION_HOME, MOTION_Z, MOTION_OFFSET,
            MOTION_TIME_STEP, MOTION_T1, MOTION_T2, MOTION_GAIN, MOTION_ALPHA,
        )
        mcfg = getattr(self, "_motion_cfg", {}) or {}
        speed_bar = float(mcfg.get("speed_bar", MOTION_SPEED_BAR))
        home = np.array(mcfg.get("home", MOTION_HOME), dtype=float)
        offset = float(mcfg.get("offset", MOTION_OFFSET)) * speed_bar
        time_step = float(mcfg.get("time_step", MOTION_TIME_STEP))
        t1 = float(mcfg.get("t1", MOTION_T1))
        t2 = float(mcfg.get("t2", MOTION_T2))
        gain = float(mcfg.get("gain", MOTION_GAIN))
        alpha = float(mcfg.get("alpha", MOTION_ALPHA))
        z = float(mcfg.get("z", MOTION_Z))
        logger.info(green(
            f"       -> move_speed_l speed_bar={speed_bar} offset={offset}"
        ))

        for _outer in range(50000):
            if self.stop_requested:
                break
            self.controller.move_speed_l(
                np.zeros(6), t1=t1, t2=t2, gain=gain, alpha=alpha
            )
            time.sleep(0.5)
            if self.stop_requested:
                break

            _x, _y, _z, _rx, _ry, _rz = home
            self.controller.move_to_point(
                np.array([_x, _y, z, _rx, _ry, _rz]), speed=100, acc=500
            )
            motions = [
                [0, offset, offset, 0, 0, 0],
                [offset, offset, 0, 0, 0, 0],
                [offset, 0, -offset, 0, 0, 0],
                [0, -offset, offset, 0, 0, 0],
                [-offset, -offset, 0, 0, 0, 0],
                [-offset, 0, -offset, 0, 0, 0],
            ]
            for _inner in range(100):
                if self.stop_requested:
                    break
                for m in motions:
                    if self.stop_requested:
                        break
                    self.controller.move_speed_l(
                        np.array(m), t1=t1, t2=t2, gain=gain, alpha=alpha
                    )
                    time.sleep(time_step)
            if self.stop_requested:
                break
            logger.info(green(f"       -> Current TCP: {self.controller.get_tcp_position()}"))

        self.controller.move_speed_l(
            np.zeros(6), t1=t1, t2=t2, gain=gain, alpha=alpha
        )
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

