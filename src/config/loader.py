"""Configuration loader from YAML file."""

import os
import yaml
from pathlib import Path
from typing import Any, Dict


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to config.yaml file. If None, uses default location.
        
    Returns:
        Dictionary containing configuration values
    """
    if config_path is None:
        # Default to config.yaml in the same directory as this file
        config_dir = Path(__file__).parent
        config_path = config_dir / "config.yaml"
    
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config


# Load configuration on import
_config = load_config()

# Expose configuration values as module-level constants for backward compatibility
ROBOT_IP = _config.get('robot_ip', '192.168.2.101')
DEFAULT_SPEED_BAR = _config.get('default_speed_bar', 1)
DEFAULT_OPERATION_MODE = _config.get('default_operation_mode', 'Simulation')

# Speed configuration
_speed_config = _config.get('speed', {})
SPEED_MULTIPLIER = _speed_config.get('speed_multiplier', 1.0)
ACCELERATION_MULTIPLIER = _speed_config.get('acceleration_multiplier', 1.0)

# Joint configuration - single values
_joint_config = _speed_config.get('joint', {})
JOINT_SPEED = _joint_config.get('speed', 100.0)  # deg/s
JOINT_ACCELERATION = _joint_config.get('acceleration', 1000.0)  # deg/s²

# Cartesian configuration - single values
_cartesian_config = _speed_config.get('cartesian', {})
CARTESIAN_LINEAR_SPEED = _cartesian_config.get('linear_speed', 100.0)  # mm/s
CARTESIAN_LINEAR_ACCELERATION = _cartesian_config.get('linear_acceleration', 1000.0)  # mm/s²
CARTESIAN_ROTATIONAL_SPEED = _cartesian_config.get('rotational_speed', 45.0)  # deg/s
CARTESIAN_ROTATIONAL_ACCELERATION = _cartesian_config.get('rotational_acceleration', 500.0)  # deg/s²

# Logger configuration
_logger_config = _config.get('logger', {})
LOGGER_LEVEL = _logger_config.get('level', 'INFO')
LOGGER_FORMAT = _logger_config.get('format', 'None')
LOGGER_COLORIZE = _logger_config.get('colorize', True)

__all__ = ['ROBOT_IP', 'DEFAULT_SPEED_BAR', 'DEFAULT_OPERATION_MODE',
           'SPEED_MULTIPLIER', 'ACCELERATION_MULTIPLIER',
           'JOINT_SPEED', 'JOINT_ACCELERATION',
           'CARTESIAN_LINEAR_SPEED', 'CARTESIAN_LINEAR_ACCELERATION',
           'CARTESIAN_ROTATIONAL_SPEED', 'CARTESIAN_ROTATIONAL_ACCELERATION',
           'LOGGER_LEVEL', 'LOGGER_FORMAT', 'LOGGER_COLORIZE', 'load_config']

