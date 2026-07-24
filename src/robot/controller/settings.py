"""Settings control methods for RobotController."""

from src.robot.controller.base import RobotController


def add_settings_methods(cls):
    """Add settings methods to RobotController class."""
    
    def set_speed_bar(self, speed_bar: float, *, timeout: float = -1.0):
        """Set robot speed bar (0~1). Optional timeout for live GUI updates."""
        self.settings.set_speed_bar(speed_bar, timeout=timeout)
    
    def set_speed_multiplier(self, multiplier: float):
        """Set speed multiplier. See RobotSettings.set_speed_multiplier() for details."""
        self.settings.set_speed_multiplier(multiplier)
    
    def set_acc_multiplier(self, multiplier: float):
        """Set acceleration multiplier. See RobotSettings.set_acc_multiplier() for details."""
        self.settings.set_acc_multiplier(multiplier)
    
    def set_speed_acc_j(self, speed: float, acceleration: float):
        """
        Set fixed joint velocity/acceleration for J-series motions.
        
        Args:
            speed: Speed/velocity in deg/s (non-negative)
            acceleration: Acceleration in deg/s² (non-negative)
        """
        self.settings.set_speed_acc_j(speed, acceleration)
    
    def set_speed_acc_l(self, speed: float, acceleration: float):
        """
        Set fixed linear velocity/acceleration for L-series motions.
        
        Args:
            speed: Speed/velocity in mm/s (non-negative)
            acceleration: Acceleration in mm/s² (non-negative)
        """
        self.settings.set_speed_acc_l(speed, acceleration)
    
    def set_collision_mode(self, mode: int):
        """Set collision detection mode. See RobotSettings.set_collision_mode() for details."""
        self.settings.set_collision_mode(mode)
    
    def set_collision_onoff(self, enable: bool):
        """Enable or disable collision detection. See RobotSettings.set_collision_onoff() for details."""
        self.settings.set_collision_onoff(enable)
    
    def set_collision_threshold(self, threshold: float):
        """Set collision detection threshold. See RobotSettings.set_collision_threshold() for details."""
        self.settings.set_collision_threshold(threshold)
    
    def set_vibrating_motion(self, *args):
        """
        Set vibrating motion parameters. See RobotSettings.set_vibrating_motion() for details.
        
        Args:
            *args: Variable arguments for the vibrating motion command
        """
        self.settings.set_vibrating_motion(*args)
    
    def enable_vibrating_motion(self):
        """Enable vibrating motion. See RobotSettings.enable_vibrating_motion() for details."""
        self.settings.enable_vibrating_motion()
    
    def disable_vibrating_motion(self):
        """Disable vibrating motion. See RobotSettings.disable_vibrating_motion() for details."""
        self.settings.disable_vibrating_motion()
    
    # Attach methods to class
    cls.set_speed_bar = set_speed_bar
    cls.set_speed_multiplier = set_speed_multiplier
    cls.set_acc_multiplier = set_acc_multiplier
    cls.set_speed_acc_j = set_speed_acc_j
    cls.set_speed_acc_l = set_speed_acc_l
    cls.set_collision_mode = set_collision_mode
    cls.set_collision_onoff = set_collision_onoff
    cls.set_collision_threshold = set_collision_threshold
    cls.set_vibrating_motion = set_vibrating_motion
    cls.enable_vibrating_motion = enable_vibrating_motion
    cls.disable_vibrating_motion = disable_vibrating_motion


add_settings_methods(RobotController)

