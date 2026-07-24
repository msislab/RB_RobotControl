"""Read stereo fx/baseline from active RealSense IR stream profiles."""

from __future__ import annotations

from typing import Any, Tuple


def read_stereo_calibration(pipeline: Any, rs_module: Any) -> Tuple[float, float]:
    """Return ``(fx_px, baseline_m)`` from IR1/IR2 extrinsics."""
    profile = pipeline.get_active_profile()
    ir1 = profile.get_stream(rs_module.stream.infrared, 1).as_video_stream_profile()
    ir2 = profile.get_stream(rs_module.stream.infrared, 2).as_video_stream_profile()
    fx = float(ir1.get_intrinsics().fx)
    baseline = abs(float(ir1.get_extrinsics_to(ir2).translation[0]))
    return fx, baseline
