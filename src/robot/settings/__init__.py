"""Robot settings package."""

from src.robot.settings.base import RobotSettings
from src.robot.settings.speed import set_speed_bar, set_speed_multiplier
from src.robot.settings.acceleration import set_acc_multiplier, set_speed_acc_j, set_speed_acc_l
from src.robot.settings.operation import (set_operation_mode, enable_waiting_ack,
                                          disable_waiting_ack, rt_script_onoff,
                                          task_stop, task_load, task_pause, task_play, task_resume)
from src.robot.settings.collision import set_collision_mode, set_collision_onoff, set_collision_threshold
from src.robot.settings.vibration import set_vibrating_motion, enable_vibrating_motion, disable_vibrating_motion

# Add functions as methods to RobotSettings class
RobotSettings.set_speed_bar = lambda self, speed_bar: set_speed_bar(self, speed_bar)
RobotSettings.set_speed_multiplier = lambda self, multiplier: set_speed_multiplier(self, multiplier)
RobotSettings.set_acc_multiplier = lambda self, multiplier: set_acc_multiplier(self, multiplier)
RobotSettings.set_speed_acc_j = lambda self, speed, acceleration: set_speed_acc_j(self, speed, acceleration)
RobotSettings.set_speed_acc_l = lambda self, speed, acceleration: set_speed_acc_l(self, speed, acceleration)
RobotSettings.set_operation_mode = lambda self, mode: set_operation_mode(self, mode)
RobotSettings.enable_waiting_ack = lambda self: enable_waiting_ack(self)
RobotSettings.disable_waiting_ack = lambda self: disable_waiting_ack(self)
RobotSettings.rt_script_onoff = lambda self, enable: rt_script_onoff(self, enable)
RobotSettings.task_stop = lambda self: task_stop(self)
RobotSettings.task_load = lambda self, task_name: task_load(self, task_name)
RobotSettings.task_pause = lambda self: task_pause(self)
RobotSettings.task_play = lambda self: task_play(self)
RobotSettings.task_resume = lambda self: task_resume(self)
RobotSettings.set_collision_mode = lambda self, mode: set_collision_mode(self, mode)
RobotSettings.set_collision_onoff = lambda self, enable: set_collision_onoff(self, enable)
RobotSettings.set_collision_threshold = lambda self, threshold: set_collision_threshold(self, threshold)
RobotSettings.set_vibrating_motion = lambda self, *args: set_vibrating_motion(self, *args)
RobotSettings.enable_vibrating_motion = lambda self: enable_vibrating_motion(self)
RobotSettings.disable_vibrating_motion = lambda self: disable_vibrating_motion(self)

__all__ = ['RobotSettings']

