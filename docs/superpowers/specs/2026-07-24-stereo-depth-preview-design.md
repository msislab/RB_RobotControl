# Stereo depth live preview — design

**Date:** 2026-07-24  
**Status:** Approved for implementation plan  
**Source:** Fast-FoundationStereo stack from `/MP/vision_system_fw` (thin port)

## Goal

Optional stereo depth from RealSense **IR1 + IR2** using Fast-FoundationStereo. Gated by a sidebar checkbox and `camera.yaml`. When enabled and Start succeeds, show a **Stereo depth** jet-heatmap pane alongside existing RealSense panes. Native RealSense depth is unchanged when the view mode includes it.

## Decisions (locked)

| Topic | Choice |
|-------|--------|
| Stereo pair | RealSense IR1 + IR2 |
| Preview | Add `stereo_depth` pane; auto-enable IR; keep RS depth when view has it |
| Assets | Copy code + weights into this repo (no `/MP` runtime dependency) |
| Checkbox lifecycle | Locked while running (set before Start) |
| Stream size | Current `camera.yaml` width/height (e.g. 640×360) |
| Approach | Thin port of `DepthEstimator`; ONNX selectable via config |

## Architecture

```
src/camera/depth/           # adapters + worker (≤200 lines each)
  depth.py                  # port of MP DepthEstimator (pytorch)
  onnx_depth.py             # ONNX Runtime backend (config-selected)
  stereo_cal.py             # fx, baseline from IR profiles
  stereo_worker.py          # load + async infer + latest heatmap
  Fast-FoundationStereo/    # upstream model repo (copied)

data/Fast-FoundationStereo_weights/
  23-36-37/                 # pytorch checkpoint (+ cfg)
  onnx/…                    # exported onnx sizes (576x960, 320x736, …)
```

| Piece | Role |
|-------|------|
| Checkbox + YAML | Enable stereo; choose backend |
| `RealSenseCamera` | Stereo on → enable IR1/IR2 at current W/H |
| Stereo worker | Load on Start (background); infer async; never block Tk |
| Preview | Extra **Stereo depth** pane when stereo started |

### Backends (`stereo_depth.backend`)

- **`pytorch`** (default) — MP `DepthEstimator` + `.pth`; native IR size (pad-to-32).
- **`onnx`** — ONNX Runtime on copied `.onnx` exports; resize IR to `onnx_size` before infer.
  Pick the export matching `variant`, `onnx_size`, and `valid_iters` (e.g. `23_36_37_iters_4_res_576x960.onnx`).

## Config & UI

### `src/config/camera.yaml`

```yaml
stereo_depth:
  enabled: false
  backend: pytorch   # pytorch | onnx
  variant: "23-36-37"
  valid_iters: 4
  z_far: 1.0
  onnx_size: "576x960"   # 576x960 | 320x736 (onnx only)
```

### Sidebar

- **Enable stereo depth** checkbox in the Camera section (same lock-while-running pattern as Enable RealSense).
- Backend / variant / onnx_size are **config-only** in v1 (no extra radios).

### Start rules

1. Stereo requires RealSense enabled — otherwise block Start with a clear message.
2. Stereo on → force IR streams on regardless of view mode.
3. View mode still controls `color` / `depth` / `ir1` / `ir2` panes; stereo adds `stereo_depth` when the worker is ready.

## Data flow

```
Start (stereo on + RS on)
  → open RealSense with IR1/IR2 at camera width/height
  → read (fx, baseline) from IR1/IR2 profiles (MP stereo_cal pattern)
  → background: load pytorch or onnx backend
  → show Stereo depth pane when ready

UI tick
  → collect frames as today
  → if stereo ready: submit latest IR1/IR2 (drop if worker busy)
  → worker: infer → jet heatmap
  → UI shows last good heatmap (may lag camera FPS)

Stop
  → stop worker; drop estimator; hide stereo pane
```

- Inference is best-effort / latest-frame (no queue buildup).
- Heatmap is **display-only** in v1 (metres map not used for motion/hand-eye).

## Errors (soft-fail)

| Case | Behavior |
|------|----------|
| Stereo on, RealSense off | Block Start with clear message |
| Missing weights / CUDA / import | Start RS without stereo pane; status/log explains why |
| IR missing mid-run | Skip stereo update; keep last heatmap or blank |
| Infer exception | Log (rate-limited); do not crash Tk |
| `backend: onnx` but export missing | Same as missing weights — disable stereo for session |

Cameras and robot remain usable when stereo fails to load.

## Testing

- Unit: config defaults → checkbox/values; preview keys include `stereo_depth` when enabled; fx/baseline reader with mocked profiles.
- Smoke (GPU): Start with stereo on → pane appears; Stop cleans up.
- Backend switch: `pytorch` vs `onnx` via YAML across Start cycles.

## Dependencies

- **pytorch** backend: CUDA PyTorch (machine-specific wheel; document in README / requirements notes, do not pin a CUDA index in the main requirements blindly).
- **onnx** backend: `onnxruntime-gpu` (or CPU ORT only if explicitly documented as unsupported for this model).
- Copy/port notes live next to weights (from MP `download_weight.md` as needed).

## Non-goals (v1)

- MP hard-fail / MQTT / IR sync error codes
- Replacing RealSense depth for robot / hand-eye
- Mid-run stereo toggle
- Sidebar radios for backend / onnx size
- Forcing 1280×720 IR when stereo is on

## File-size / SRP

New application modules ≤200 lines. Copied upstream `Fast-FoundationStereo/` and a near-verbatim `depth.py` may exceed that as vendor ports; split only when we heavily edit them.
