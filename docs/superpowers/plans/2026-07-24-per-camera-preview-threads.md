# Per-camera preview threads — implementation plan

> **For agentic workers:** implement task-by-task; keep app sources ≤200 lines.

**Goal:** Independent capture threads per camera + per-pane FPS.

**Tech:** threading + `FrameHub`; Tk updates only via `root.after`.

## File map

| File | Role |
|------|------|
| `src/camera/frame_hub.py` | Thread-safe latest frame + generation per key; `wait_new` |
| `src/camera/capture_pool.py` | Start/stop RS + per-Omron capture threads; stereo publish |
| `src/camera/pane_workers.py` | One worker per preview key → schedule UI apply |
| `src/camera/omron_camera.py` | Add `read_one(cid)` |
| `src/camera/gui_fps.py` | Tick only updated keys |
| `src/camera/gui_run.py` / `display_gui.py` | Start pool on run; stop on halt; drop monolithic `_schedule_frame` read |

## Tasks

### Task 1: FrameHub
- Create hub with `publish(key, frame)`, `snapshot(key)`, `wait_new(key, after_gen, timeout)`.

### Task 2: Omron `read_one`
- Read single device row by `cid`.

### Task 3: CapturePool
- RS loop → publish each returned key; submit IR to stereo; publish heatmap when new.
- Omron: thread per `cid` → `read_one` → publish.
- `start(gui)` / `stop()`.

### Task 4: Pane workers + FPS
- Per active key: wait_new → `root.after(0, apply_pane)`.
- `apply_pane` fits, PhotoImage, `fps_board.tick_key`.

### Task 5: Wire GUI
- On start ok: build hub, start pool + pane workers.
- On stop: stop workers/pool before detaching cameras.

### Task 6: Smoke
- `python -c` imports; confirm no conflict markers; line counts ≤200.
