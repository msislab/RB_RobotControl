"""Omron GenICam Gain limits (Sentech analog often 0–20.8 dB → 0–208)."""

from __future__ import annotations

from typing import Any, Tuple

from loguru import logger

from src.camera.omron_nodes import numeric_range
from src.utils.color import green

DEFAULT_GAIN_MAX = 208.0
_gain_min = 0.0
_gain_max = DEFAULT_GAIN_MAX


def get_omron_gain_limits() -> Tuple[float, float]:
    return _gain_min, _gain_max


def clamp_gain(gain: float) -> float:
    return max(_gain_min, min(_gain_max, float(gain)))


def probe_gain_limits(api: Any, device: Any) -> Tuple[float, float]:
    global _gain_min, _gain_max
    rng = numeric_range(api, device.remote_port.nodemap, "Gain")
    if rng is None:
        logger.info("Omron Gain range unavailable — using 0–{}", DEFAULT_GAIN_MAX)
        return _gain_min, _gain_max
    _gain_min, _gain_max = float(rng[0]), float(rng[1])
    logger.info(green(f"Omron Gain range: {_gain_min:g} … {_gain_max:g}"))
    return _gain_min, _gain_max
