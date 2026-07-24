# Stereo Depth Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline; user asked to implement immediately). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add checkbox + YAML-gated Fast-FoundationStereo live preview from RealSense IR1/IR2, with pytorch default and onnx selectable from config.

**Architecture:** Copy MP model repo + weights into this tree; thin `DepthEstimator` / ONNX adapters + async `StereoWorker`; wire RealSense `force_ir`, sidebar checkbox, and a `stereo_depth` preview pane. Soft-fail if CUDA/weights/ORT missing.

**Tech Stack:** pyrealsense2, Tkinter, PyTorch CUDA, optional onnxruntime-gpu, OpenCV.

## Global Constraints

- Application source ≤200 lines per file (vendor `Fast-FoundationStereo/` and near-verbatim `depth.py` exempt as ports).
- Stereo pair = RealSense IR1/IR2 at current camera W/H.
- Checkbox locked while running; backend/onnx_size config-only.
- Soft-fail stereo load; do not block cameras/robot when stereo fails.
- This branch uses `src/config/config.yaml` `camera:` (not a split `camera.yaml`).
- Do not commit unless the user asks.

---

### Task 1: Copy assets from `/MP`

**Files:**
- Create: `src/camera/depth/Fast-FoundationStereo/` (copy)
- Create: `data/Fast-FoundationStereo_weights/23-36-37/` (copy)
- Create: `data/Fast-FoundationStereo_weights/onnx/23_36_37/{576x960,320x736}/` (.onnx + .yaml only; skip `.engine`)

- [ ] **Step 1:** `mkdir -p` and `rsync` from `/MP/vision_system_fw/...` excluding `__pycache__`, `.git`, `docker`, `output_docker`.
- [ ] **Step 2:** Verify `model_best_bp2_serialize.pth` and at least one `*_iters_4_res_576x960.onnx` exist.

---

### Task 2: Depth core modules

**Files:**
- Create: `src/camera/depth/__init__.py`
- Create: `src/camera/depth/stereo_cal.py` — `read_stereo_calibration(pipeline, rs) -> (fx, baseline)`
- Create: `src/camera/depth/depth.py` — port MP `DepthEstimator`; paths → repo `data/`; use `src.utils.color`; no-op timing; ctor args `input_h/input_w` for warmup
- Create: `src/camera/depth/onnx_depth.py` — `OnnxDepthEstimator` (ORT single-onnx; ImageNet norm; resize to export size; jet heatmap)
- Create: `src/camera/depth/stereo_worker.py` — load backend on thread; `submit(ir1, ir2)`; `latest_heatmap()`; `stop()`
- Create: `src/camera/depth/factory.py` — `build_estimator(cfg) -> estimator` (`backend` pytorch|onnx)

**Interfaces:**
- Produces: `estimator.process(left, right, fx, baseline) -> (heatmap_bgr|None, depth_m)`
- Produces: `StereoWorker(fx, baseline, cfg).start_load()` / `.submit` / `.latest_heatmap` / `.ready` / `.error` / `.stop`

- [ ] Implement modules (≤200 lines each except ported depth.py if needed).
- [ ] Smoke-import `stereo_cal` without GPU.

---

### Task 3: RealSense IR + calibration

**Files:**
- Modify: `src/camera/realsense_camera.py`

- [ ] Add `force_ir: bool = False`; `want_ir` true when view has IR **or** `force_ir`.
- [ ] After `pipeline.start`, if `want_ir`, store `(fx, baseline)` via `stereo_cal`.
- [ ] `read()`: on missing IR, omit ir keys (do not raise) when only `force_ir`; still provide `ir1`/`ir2` BGR when present; also attach raw gray as used by worker (convert from gray in worker from BGR is OK).
- [ ] Expose `stereo_fx` / `stereo_baseline` properties.

---

### Task 4: Config + UI + preview wiring

**Files:**
- Modify: `src/config/config.yaml` — add `camera.stereo_depth` block
- Modify: `src/config/loader.py` — expose stereo defaults into constants / nested dict
- Modify: `src/main.py` — pass stereo defaults
- Modify: `src/camera/gui_settings.py` — Enable stereo depth checkbox + values
- Modify: `src/camera/gui_shell.py` — pane `stereo_depth` / title `Stereo depth`
- Create: `src/camera/gui_stereo.py` — panel key list, start/stop worker helpers (keep `display_gui` ≤200)
- Modify: `src/camera/display_gui.py` — Start validation, worker lifecycle, tick submit/show
- Modify: `requirements.txt` if present — note torch (existing) + optional `onnxruntime-gpu`

- [ ] Start with stereo+no RS → error status, no start.
- [ ] Start with stereo+RS → force IR, load worker, show pane when ready; soft-fail → status message, RS still runs.
- [ ] Stop → worker stop, unlock checkbox.

---

### Task 5: Verify

- [ ] `python -c` import depth package / factory with `enabled` path mocked.
- [ ] Line counts ≤200 for new app modules.
- [ ] Update `memory.md` in-progress/completed.

---

## Spec coverage

| Spec item | Task |
|-----------|------|
| Copy code+weights | 1 |
| pytorch + onnx backends | 2 |
| IR1/IR2, fx/baseline | 3 |
| Checkbox + YAML + pane + async | 4 |
| Soft-fail / testing | 4–5 |
