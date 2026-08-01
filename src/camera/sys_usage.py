"""Sample host RAM, CPU, and GPU0 VRAM usage percentages."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class SysUsage:
    """Percent used in [0, 100]; None when a sensor is unavailable."""

    ram: Optional[float]
    cpu: Optional[float]
    gpu_vram: Optional[float]


_nvml_ok: Optional[bool] = None
_cpu_primed = False


def _ram_percent() -> Optional[float]:
    try:
        import psutil
    except ImportError:
        return None
    return float(psutil.virtual_memory().percent)


def _cpu_percent() -> Optional[float]:
    global _cpu_primed
    try:
        import psutil
    except ImportError:
        return None
    # First call primes; non-blocking thereafter (interval=None).
    pct = float(psutil.cpu_percent(interval=None))
    if not _cpu_primed:
        _cpu_primed = True
        return 0.0
    return pct


def _gpu0_vram_percent() -> Optional[float]:
    global _nvml_ok
    if _nvml_ok is False:
        return None
    try:
        import pynvml
    except ImportError:
        _nvml_ok = False
        return None
    try:
        if _nvml_ok is None:
            pynvml.nvmlInit()
            _nvml_ok = True
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        if not info.total:
            return None
        return 100.0 * float(info.used) / float(info.total)
    except Exception:
        _nvml_ok = False
        return None


def sample_sys_usage() -> SysUsage:
    """Non-blocking sample suitable for a Tk after() poll."""
    return SysUsage(
        ram=_ram_percent(),
        cpu=_cpu_percent(),
        gpu_vram=_gpu0_vram_percent(),
    )


def as_triplet(usage: SysUsage) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    return usage.ram, usage.cpu, usage.gpu_vram
