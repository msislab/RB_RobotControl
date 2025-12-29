"""Handles data collection from the robot in a separate thread."""

import time
import threading
from typing import Optional
import rbpodo as rb
from loguru import logger
from src.utils.color import green

class DataCollector:
    """Handles data collection from the robot in a separate thread."""
    
    def __init__(self, robot_ip: str):
        """
        Initialize the data collector.
        
        Args:
            robot_ip: IP address of the robot controller
        """
        self.robot_ip = robot_ip
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.data_channel: Optional[rb.CobotData] = None
    
    def start(self):
        """Start the data collection thread."""
        if self.thread is not None and self.thread.is_alive():
            logger.warning("Data collector thread is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._collect_data, daemon=True)
        self.thread.start()
        logger.info(green("       -> Data collector thread started"))
    
    def stop(self, timeout: float = 2.0):
        """Stop the data collection thread."""
        self.running = False
        if self.thread is not None:
            self.thread.join(timeout=timeout)
            logger.info(green("       -> Data collector thread stopped"))
    
    def _collect_data(self):
        """Internal method that runs in the data collection thread."""
        try:
            self.data_channel = rb.CobotData(self.robot_ip)
            while self.running:
                data = self.data_channel.request_data()
                self.data = data.sdata
                time.sleep(0.1)
        except Exception as e:
            logger.error("Error in data collection thread: {}", e)

