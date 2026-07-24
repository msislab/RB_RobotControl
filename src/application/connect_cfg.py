"""Apply GUI/YAML settings on an existing or new robot connection (with step logs)."""

from __future__ import annotations

import threading
from typing import Any

from loguru import logger

from src.robot.controller import RobotController
from src.utils.color import green, yellow


def _step(msg: str) -> None:
    logger.info(yellow(f"       -> [robot-cfg] {msg}"))


_CONNECT_LOCK_TIMEOUT_S = 5.0


def connect_with_settings(app: Any, cfg: dict) -> None:
    """Connect/reconnect and apply settings; leave motion idle (no routine)."""
    _step(f"waiting for connect lock (thread={threading.current_thread().name})")
    if not app._connect_lock.acquire(timeout=_CONNECT_LOCK_TIMEOUT_S):
        raise RuntimeError(
            "Robot connect busy (previous setup still running); Stop and retry"
        )
    try:
        _step("connect lock acquired")
        ip = (cfg.get("robot_ip") or app.robot_ip).strip()
        need_connect = not getattr(app, "_setup_done", False) or ip != app.robot_ip
        _step(
            f"need_connect={need_connect} ip={ip!r} "
            f"setup_done={getattr(app, '_setup_done', False)}"
        )
        if need_connect:
            if getattr(app, "_setup_done", False):
                _step("stopping previous controller before reconnect")
                try:
                    app.controller.stop()
                    _step("previous controller stopped")
                except Exception as e:
                    logger.warning("Stop before reconnect: {}", e)
            app.robot_ip = ip
            _step(f"creating RobotController({ip!r})")
            app.controller = RobotController(ip)
            _step("controller.connect()…")
            app.controller.connect()
            _step("controller.initialize()…")
            app.controller.initialize()
            app._setup_done = True
            _step("connect+initialize done")

        mode = cfg.get("operation_mode")
        if mode:
            _step(f"set_operation_mode({mode!r})…")
            app.controller.settings.set_operation_mode(mode)
            _step("set_operation_mode done")
        else:
            _step("skip operation_mode (none)")

        js = float(cfg.get("joint_speed", 180.0))
        ja = float(cfg.get("joint_acc", 180.0))
        _step(f"set_speed_acc_j(speed={js}, acc={ja})…")
        app.controller.set_speed_acc_j(js, ja)
        _step("set_speed_acc_j done")

        ls = float(cfg.get("linear_speed", 1000.0))
        la = float(cfg.get("linear_acc", 1000.0))
        _step(f"set_speed_acc_l(speed={ls}, acc={la})…")
        app.controller.set_speed_acc_l(ls, la)
        _step("set_speed_acc_l done")

        sm = float(cfg.get("speed_multiplier", 1.0))
        _step(f"set_speed_multiplier({sm})…")
        app.controller.set_speed_multiplier(sm)
        _step("set_speed_multiplier done")

        am = float(cfg.get("acceleration_multiplier", 1.0))
        _step(f"set_acc_multiplier({am})…")
        app.controller.set_acc_multiplier(am)
        _step("set_acc_multiplier done")

        from src.config.loader import DEFAULT_SPEED_BAR

        sb = float(cfg.get("speed_bar", DEFAULT_SPEED_BAR))
        _step(f"set_speed_bar({sb})…")
        app.controller.set_speed_bar(sb)
        _step("set_speed_bar done")

        _step("task_resume(collision=True)…")
        try:
            app.controller.task_resume(collision=True)
            _step("task_resume done")
        except Exception as e:
            logger.warning("Collision resume on connect failed: {}", e)

        app._motion_cfg = dict(cfg)
        app.running = False
        app.stop_requested = False
        logger.info(green("       -> Robot connected (idle)"))
    finally:
        app._connect_lock.release()
        _step("connect lock released")
