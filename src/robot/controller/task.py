"""Task control methods for RobotController."""

from src.robot.controller.base import RobotController


def add_task_methods(cls):
    """Add task control methods to RobotController class."""
    
    def task_stop(self):
        """Stop robot tasks. See RobotSettings.task_stop() for details."""
        self.settings.task_stop()
    
    def task_load(self, task_name: str):
        """Load a task program. See RobotSettings.task_load() for details."""
        self.settings.task_load(task_name)
    
    def task_pause(self):
        """Pause the current task. See RobotSettings.task_pause() for details."""
        self.settings.task_pause()
    
    def task_play(self):
        """Play/start the current task. See RobotSettings.task_play() for details."""
        self.settings.task_play()
    
    def task_resume(self):
        """Resume the paused task. See RobotSettings.task_resume() for details."""
        self.settings.task_resume()
    
    # Attach methods to class
    cls.task_stop = task_stop
    cls.task_load = task_load
    cls.task_pause = task_pause
    cls.task_play = task_play
    cls.task_resume = task_resume


add_task_methods(RobotController)

