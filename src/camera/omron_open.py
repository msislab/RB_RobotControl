"""Per-device Omron freerun open (minimal GenICam writes)."""

from __future__ import annotations

import time
from typing import Any, Tuple

from loguru import logger

from src.camera.omron_nodes import set_enumeration, set_max_roi, set_numeric
from src.utils.color import green


def _step(label: str, t_prev: float) -> float:
    now = time.monotonic()
    dt = now - t_prev
    if dt >= 0.05:
        logger.info("Omron step {}: {:.2f}s", label, dt)
    return now


def device_serial(device: Any) -> str:
    try:
        return str(device.info.serial_number)
    except Exception:
        return ""


def open_freerun(
    api: Any,
    index: int,
    device: Any,
    *,
    exposure: float,
    gain: float,
    detail: bool = False,
) -> Tuple[str, Any, Any, Any]:
    """Start freerun RGB at sensor max ROI (once at process start; slow on GigE)."""
    cid = f"omron_{index}"
    serial = device_serial(device) or cid
    t0 = time.monotonic()
    t = t0
    nodemap = device.remote_port.nodemap
    if detail:
        t = _step(f"{cid} nodemap", t)
    roi = set_max_roi(api, nodemap)
    if detail:
        t = _step(f"{cid} max ROI {roi}", t)
    set_enumeration(api, nodemap, "TriggerMode", "Off")
    if detail:
        t = _step(f"{cid} TriggerMode", t)
    set_enumeration(api, nodemap, "GainAuto", "Off")
    set_enumeration(api, nodemap, "ExposureAuto", "Off")
    if detail:
        t = _step(f"{cid} AutoOff", t)
    set_numeric(api, nodemap, "Gain", gain)
    set_numeric(api, nodemap, "ExposureTime", exposure)
    if detail:
        t = _step(f"{cid} exposure/gain", t)
    stream = device.create_datastream()
    converter = api.create_converter(api.EStConverterType.PixelFormat)
    converter.destination_pixel_format = api.EStPixelFormatNamingConvention.BGR8
    if detail:
        t = _step(f"{cid} datastream/converter", t)
    stream.start_acquisition()
    if detail:
        t = _step(f"{cid} start_acquisition", t)
    device.acquisition_start()
    if detail:
        _step(f"{cid} acquisition_start", t)
    logger.info(
        green(
            f"Omron connected: {cid} serial={serial} roi={roi} "
            f"({time.monotonic() - t0:.2f}s)"
        )
    )
    return cid, device, stream, converter
