"""Load per-component YAML files from src/config/ into one dict."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

CONFIG_DIR = Path(__file__).parent

# Nested under their filename (without .yaml). robot.yaml merges at root.
_NESTED_COMPONENTS: List[str] = [
    "speed",
    "motion",
    "logger",
    "camera",
    "omron",
]


def _read_yaml(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_yaml_file(name: str, config_dir: Optional[Path] = None) -> Any:
    """Load `{name}.yaml` from the config directory."""
    root = config_dir or CONFIG_DIR
    return _read_yaml(root / f"{name}.yaml")


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Merge component YAML files into one dict (same shape as the old config.yaml).

    If ``config_path`` points at a legacy monolithic ``config.yaml``, that file
    is loaded instead. Otherwise loads ``robot.yaml`` + nested components.
    """
    if config_path is not None:
        path = Path(config_path)
        data = _read_yaml(path)
        if not isinstance(data, dict):
            raise ValueError(f"Config root must be a mapping: {path}")
        return data

    config_dir = CONFIG_DIR
    legacy = config_dir / "config.yaml"
    if legacy.exists() and not (config_dir / "robot.yaml").exists():
        data = _read_yaml(legacy)
        if not isinstance(data, dict):
            raise ValueError(f"Config root must be a mapping: {legacy}")
        return data

    robot = _read_yaml(config_dir / "robot.yaml") or {}
    if not isinstance(robot, dict):
        raise ValueError("robot.yaml root must be a mapping")
    config: Dict[str, Any] = dict(robot)
    for name in _NESTED_COMPONENTS:
        payload = _read_yaml(config_dir / f"{name}.yaml")
        config[name] = payload if payload is not None else {}
    return config


# Load configuration on import
_config = load_config()

# Expose configuration values as module-level constants for backward compatibility
ROBOT_IP = _config.get("robot_ip", "192.168.2.101")
ROBOT_ENABLED = bool(_config.get("robot_enabled", True))
ROBOT_ROUTINE = str(_config.get("robot_routine", "zigzag")).strip().lower()
ROBOT_SEQUENCE = str(_config.get("robot_sequence", "ket")).strip()
ROBOT_SEQUENCE_LOOP = bool(_config.get("robot_sequence_loop", False))
ROBOT_SEQUENCE_MERGE = bool(_config.get("robot_sequence_merge", False))
DEFAULT_SPEED_BAR = _config.get("default_speed_bar", 1)
DEFAULT_OPERATION_MODE = _config.get("default_operation_mode", "Simulation")

_speed_config = _config.get("speed", {}) or {}
SPEED_MULTIPLIER = _speed_config.get("speed_multiplier", 1.0)
ACCELERATION_MULTIPLIER = _speed_config.get("acceleration_multiplier", 1.0)

_joint_config = _speed_config.get("joint", {}) or {}
JOINT_SPEED = _joint_config.get("speed", 100.0)
JOINT_ACCELERATION = _joint_config.get("acceleration", 1000.0)

_cartesian_config = _speed_config.get("cartesian", {}) or {}
CARTESIAN_LINEAR_SPEED = _cartesian_config.get("linear_speed", 100.0)
CARTESIAN_LINEAR_ACCELERATION = _cartesian_config.get("linear_acceleration", 1000.0)
CARTESIAN_ROTATIONAL_SPEED = _cartesian_config.get("rotational_speed", 45.0)
CARTESIAN_ROTATIONAL_ACCELERATION = _cartesian_config.get(
    "rotational_acceleration", 500.0
)

_logger_config = _config.get("logger", {}) or {}
LOGGER_LEVEL = _logger_config.get("level", "INFO")
LOGGER_FORMAT = _logger_config.get("format", "None")
LOGGER_COLORIZE = _logger_config.get("colorize", True)

_camera_config = _config.get("camera", {}) or {}
CAMERA_ENABLED = bool(_camera_config.get("enabled", False))
CAMERA_VIEW = _camera_config.get("view", "rgb")
CAMERA_FPS = int(_camera_config.get("fps", 30))
CAMERA_SERIAL = _camera_config.get("serial", None)
CAMERA_WIDTH = int(_camera_config.get("width", 640))
CAMERA_HEIGHT = int(_camera_config.get("height", 360))
CAMERA_EXPOSURE = float(_camera_config.get("exposure", 100))
CAMERA_GAIN = float(_camera_config.get("gain", 16))

_omron_config = _config.get("omron", {}) or {}
OMRON_ENABLED = bool(_omron_config.get("enabled", False))
OMRON_FPS = int(_omron_config.get("fps", CAMERA_FPS))
OMRON_EXPOSURE = float(_omron_config.get("exposure", 500))
OMRON_GAIN = float(_omron_config.get("gain", 200))
OMRON_IP_POOL_CIDR = str(_omron_config.get("ip_pool_cidr", "192.168.2.192/27"))
OMRON_PREFERRED_IPS = list(_omron_config.get("preferred_ips") or [])

_motion = _config.get("motion", {}) or {}
MOTION_SPEED_BAR = float(_motion.get("speed_bar", 1.0))
MOTION_HOME = list(_motion.get("home", [-300.0, -450.0, 350.0, 90.0, 0.0, 0.0]))
MOTION_Z = float(_motion.get("z", 350.0))
MOTION_OFFSET = float(_motion.get("offset", 600.0))
MOTION_TIME_STEP = float(_motion.get("time_step", 0.1))
MOTION_T1 = float(_motion.get("t1", 0.08))
MOTION_T2 = float(_motion.get("t2", 0.03))
MOTION_GAIN = float(_motion.get("gain", 0.5))
MOTION_ALPHA = float(_motion.get("alpha", 0.05))

__all__ = [
    "ROBOT_IP",
    "ROBOT_ENABLED",
    "ROBOT_ROUTINE",
    "ROBOT_SEQUENCE",
    "ROBOT_SEQUENCE_LOOP",
    "ROBOT_SEQUENCE_MERGE",
    "DEFAULT_SPEED_BAR",
    "DEFAULT_OPERATION_MODE",
    "SPEED_MULTIPLIER",
    "ACCELERATION_MULTIPLIER",
    "JOINT_SPEED",
    "JOINT_ACCELERATION",
    "CARTESIAN_LINEAR_SPEED",
    "CARTESIAN_LINEAR_ACCELERATION",
    "CARTESIAN_ROTATIONAL_SPEED",
    "CARTESIAN_ROTATIONAL_ACCELERATION",
    "LOGGER_LEVEL",
    "LOGGER_FORMAT",
    "LOGGER_COLORIZE",
    "CAMERA_ENABLED",
    "CAMERA_VIEW",
    "CAMERA_FPS",
    "CAMERA_SERIAL",
    "CAMERA_WIDTH",
    "CAMERA_HEIGHT",
    "CAMERA_EXPOSURE",
    "CAMERA_GAIN",
    "OMRON_ENABLED",
    "OMRON_FPS",
    "OMRON_EXPOSURE",
    "OMRON_GAIN",
    "OMRON_IP_POOL_CIDR",
    "OMRON_PREFERRED_IPS",
    "MOTION_SPEED_BAR",
    "MOTION_HOME",
    "MOTION_Z",
    "MOTION_OFFSET",
    "MOTION_TIME_STEP",
    "MOTION_T1",
    "MOTION_T2",
    "MOTION_GAIN",
    "MOTION_ALPHA",
    "CONFIG_DIR",
    "load_config",
    "load_yaml_file",
]
