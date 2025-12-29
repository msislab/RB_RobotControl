"""ICV control methods for RobotController."""

from src.robot.controller.base import RobotController


def add_icv_methods(cls):
    """Add ICV methods to RobotController class."""
    
    def enable_icv(self):
        """Enable Imaginary Conveyor mode."""
        self.icv.enable()
    
    def disable_icv(self):
        """Disable Imaginary Conveyor mode."""
        self.icv.disable()
    
    def icv_set(self, t_sec: float, frame: int, x_mm: float, y_mm: float, 
                z_mm: float, rx_deg: float = 0.0, ry_deg: float = 0.0, 
                rz_deg: float = 0.0, mode: int = 0):
        """Set ICV parameters. See RobotICV.set() for details."""
        self.icv.set(t_sec, frame, x_mm, y_mm, z_mm, rx_deg, ry_deg, rz_deg, mode)
    
    # Attach methods to class
    cls.enable_icv = enable_icv
    cls.disable_icv = disable_icv
    cls.icv_set = icv_set


add_icv_methods(RobotController)

