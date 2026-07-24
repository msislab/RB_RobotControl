"""Thin RealSense capture for live display (no save)."""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import numpy as np
import pyrealsense2 as rs

from src.camera.depth.stereo_cal import read_stereo_calibration

VIEW_RGB = "rgb"
VIEW_RGB_DEPTH = "rgb_depth"
VIEW_RGB_DEPTH_IR = "rgb_depth_ir"
VALID_VIEWS = (VIEW_RGB, VIEW_RGB_DEPTH, VIEW_RGB_DEPTH_IR)


class RealSenseCamera:
    """Start/stop RealSense and grab frames for the selected view mode."""

    def __init__(
        self,
        view: str = VIEW_RGB,
        fps: int = 30,
        serial: Optional[str] = None,
        width: int = 640,
        height: int = 360,
        exposure: float = 100.0,
        gain: float = 16.0,
        force_ir: bool = False,
    ) -> None:
        if view not in VALID_VIEWS:
            raise ValueError(f"view must be one of {VALID_VIEWS}, got {view!r}")
        self.view = view
        self.fps = fps
        self.serial = serial
        self.width = width
        self.height = height
        self.exposure = float(exposure)
        self.gain = float(gain)
        self.force_ir = bool(force_ir)
        self._pipeline: Optional[rs.pipeline] = None
        self._align: Optional[rs.align] = None
        self._color_sensor = None
        self._stereo_fx: Optional[float] = None
        self._stereo_baseline: Optional[float] = None

    @property
    def want_depth(self) -> bool:
        return self.view in (VIEW_RGB_DEPTH, VIEW_RGB_DEPTH_IR)

    @property
    def want_ir(self) -> bool:
        return self.view == VIEW_RGB_DEPTH_IR or self.force_ir

    @property
    def stereo_calibration(self) -> Optional[Tuple[float, float]]:
        if self._stereo_fx is None or self._stereo_baseline is None:
            return None
        return self._stereo_fx, self._stereo_baseline

    def start(self) -> None:
        if self._pipeline is not None:
            return
        pipeline = rs.pipeline()
        config = rs.config()
        if self.serial:
            config.enable_device(self.serial)
        config.enable_stream(
            rs.stream.color, self.width, self.height, rs.format.bgr8, self.fps
        )
        if self.want_depth:
            config.enable_stream(
                rs.stream.depth, self.width, self.height, rs.format.z16, self.fps
            )
        if self.want_ir:
            config.enable_stream(
                rs.stream.infrared, 1, self.width, self.height, rs.format.y8, self.fps
            )
            config.enable_stream(
                rs.stream.infrared, 2, self.width, self.height, rs.format.y8, self.fps
            )
        profile = pipeline.start(config)
        self._pipeline = pipeline
        self._align = rs.align(rs.stream.color) if self.want_depth else None
        try:
            for sensor in profile.get_device().query_sensors():
                if sensor.supports(rs.option.enable_auto_exposure):
                    self._color_sensor = sensor
                    break
        except Exception:
            self._color_sensor = None
        self.set_exposure_gain(self.exposure, self.gain)
        self._stereo_fx = self._stereo_baseline = None
        if self.want_ir:
            self._stereo_fx, self._stereo_baseline = read_stereo_calibration(
                pipeline, rs
            )

    def set_exposure_gain(self, exposure: float, gain: float) -> None:
        """Apply manual exposure (µs) and gain while streaming."""
        self.exposure = float(exposure)
        self.gain = float(gain)
        sensor = self._color_sensor
        if sensor is None:
            return
        try:
            if sensor.supports(rs.option.enable_auto_exposure):
                sensor.set_option(rs.option.enable_auto_exposure, 0)
            if sensor.supports(rs.option.exposure):
                sensor.set_option(rs.option.exposure, self.exposure)
            if sensor.supports(rs.option.gain):
                sensor.set_option(rs.option.gain, self.gain)
        except Exception:
            pass

    def stop(self) -> None:
        pipeline = self._pipeline
        self._pipeline = None
        self._align = None
        self._color_sensor = None
        self._stereo_fx = self._stereo_baseline = None
        if pipeline is not None:
            try:
                pipeline.stop()
            except Exception:
                pass

    def read(self) -> Dict[str, np.ndarray]:
        """Return dict with keys among: color, depth, ir1, ir2 (BGR/uint8 for display)."""
        if self._pipeline is None:
            raise RuntimeError("Camera not started")
        # Short wait — miss a tick rather than freeze the Tk UI for seconds.
        frames = self._pipeline.poll_for_frames()
        if not frames:
            frames = self._pipeline.wait_for_frames(100)
        if not frames:
            return {}
        ir1 = ir2 = None
        if self.want_ir:
            ir1 = frames.get_infrared_frame(1)
            ir2 = frames.get_infrared_frame(2)
            # Missing IR must not drop RGB/depth — stereo feeder just waits.

        view = frames
        if self._align is not None:
            view = self._align.process(frames)

        out: Dict[str, np.ndarray] = {}
        color = view.get_color_frame()
        if not color:
            return {}
        out["color"] = np.asanyarray(color.get_data())

        if self.want_depth:
            depth = view.get_depth_frame()
            if depth:
                out["depth"] = _depth_to_bgr(np.asanyarray(depth.get_data()))

        if ir1 and ir2:
            out["ir1"] = _gray_to_bgr(np.asanyarray(ir1.get_data()))
            out["ir2"] = _gray_to_bgr(np.asanyarray(ir2.get_data()))
        return out


def _depth_to_bgr(depth: np.ndarray) -> np.ndarray:
    import cv2

    scaled = cv2.convertScaleAbs(depth, alpha=0.03)
    return cv2.applyColorMap(scaled, cv2.COLORMAP_JET)


def _gray_to_bgr(gray: np.ndarray) -> np.ndarray:
    import cv2

    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
