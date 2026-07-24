# Device actual FPS on preview titles — design

Date: 2026-07-24

## Goal

Show **live device-reported** FPS next to measured preview FPS and config target:

`RGB — 12 / cam 28 (cfg 30)`

If the device does not expose a live actual rate: `cam —`.

## Sources

| Camera | Source | Notes |
|--------|--------|--------|
| RealSense | `frame_metadata_value.actual_fps` | Per stream when supported; metadata is **Hz×1000** (divide by 1000). ≤0 → missing |
| Omron | GenICam `ResultingFrameRate` | Only this live node; **not** `AcquisitionFrameRate` (setpoint). Probe once; throttle reads ~1 Hz |
| Stereo depth | none | Always `cam —` |

## Architecture

```
RealSense.read / Omron.read_one
  → last_device_fps[key] (optional float)
CapturePool
  → DeviceFpsStore.set(key, fps|None) on publish
Pane on_frame
  → CameraFpsBoard.tick_key → title format
```

## Rules

- Never invent cam FPS from capture-thread counts or negotiated profile rates.
- Measured FPS remains per-pane preview update rate.
- Config target remains the GUI FPS setting (`cfg`).

## Non-goals

- Changing capture pacing or stream config from this display.
- Showing negotiated profile FPS as `cam`.
