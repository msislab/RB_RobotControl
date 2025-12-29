"""Script control methods for RobotController."""

from src.robot.controller.base import RobotController


def add_script_methods(cls):
    """Add script methods to RobotController class."""
    
    def send_script(self, cmd: str) -> int:
        """Send a script command. See RobotScript.send_script() for details."""
        return self.script.send_script(cmd)
    
    def run_script(self, script: str, enable_rt: bool = True, disable_rt: bool = True):
        """Run a script. See RobotScript.run_script() for details."""
        self.script.run_script(script, enable_rt, disable_rt)
    
    # Attach methods to class
    cls.send_script = send_script
    cls.run_script = run_script


add_script_methods(RobotController)

