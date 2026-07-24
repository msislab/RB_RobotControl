# Per-camera preview threads — design

Date: 2026-07-24

## Goal

- Each **camera** captures on its own thread (1× RealSense, 1× per Omron).
- Extra **worker** threads allowed (per-pane display prep, stereo already threaded).
- Each preview pane’s FPS is measured independently (tick only when that pane gets a new frame).

## Architecture

```
RealSense thread ──┐
Omron cam A thread─┼─► FrameHub (per-key frame + generation)
Omron cam B thread─┘         │
                    StereoFeed thread ◄── reads ir1/ir2 from hub
                              │          submits / consume_heatmap
StereoWorker (infer) ─────────┘ publishes stereo_depth
                              │
                    PaneWorker × N (one per active key)
```

## Rules

- No `camera.read()` / Omron retrieve on the Tk thread while running.
- RealSense capture loop only publishes frames — stereo submit/heatmap is `StereoFeed` only.
- Missing IR must not drop RGB/depth from RealSense `read()`.
- FPS title format stays `NAME — measured/target`; meters never tick for other keys in the same call.
- Stop/close: stop event → join capture + pane workers (short timeout) → detach cameras.

## Non-goals

- Multiple RealSense devices.
- Changing stereo model load path (keep `StereoWorker`).
