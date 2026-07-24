# Live Speed Bar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep the Speed bar usable while Running; debounce-apply robot `set_speed_bar` and refresh ZigZag `offset * speed_bar` on the next ZigZag step.

**Architecture:** Exclude the Speed bar Scale from Start lockables. On drag, debounce (~150 ms) like exposure: update `app._motion_cfg["speed_bar"]` and call `controller.set_speed_bar` on a worker thread when connected. ZigZag recomputes offset each outer loop from `_motion_cfg`.

**Tech Stack:** Tkinter, loguru, existing `RobotController.set_speed_bar`, `SettingsPanel` / `gui_motion`.

## Global Constraints

- Application source files ≤ **200 lines** (split if needed).
- Do **not** edit locked `src/config/*.yaml` unless the user asks in the same task.
- Do **not** unlock Speed/Acc multiplier radios.
- Do **not** abort in-flight MoveXB when the bar moves.
- Do **not** commit unless the user explicitly asks.
- Spec: `docs/superpowers/specs/2026-07-24-live-speed-bar-design.md`.

## File map

| File | Role |
|------|------|
| `src/camera/gui_motion.py` | Speed bar not lockable; optional `on_speed_bar_change(n: float)` |
| `src/camera/gui_settings.py` | Pass callback; hint text; optional `_speed_bar_scale` (no lock) |
| `src/camera/gui_shell.py` | Thread `on_speed_bar_change` into `SettingsPanel` |
| `src/camera/live_speed_bar.py` | **Create** — debounce helper + apply (cfg + robot) so `display_gui` stays ≤200 |
| `src/camera/display_gui.py` | Wire schedule/apply to live_speed_bar |
| `src/application/application.py` | ZigZag: re-read bar/offset each outer loop; rebuild motions |

---

### Task 1: Unlock Speed bar + change callback

**Files:**
- Modify: `src/camera/gui_motion.py`
- Modify: `src/camera/gui_settings.py`
- Modify: `src/camera/gui_shell.py`

**Interfaces:**
- Consumes: existing `build_motion_section(parent, defaults, lockable)`
- Produces: `build_motion_section(..., on_speed_bar_change: Optional[Callable[[float], None]] = None)`; Scale **not** appended to `lockable`; `_on_bar` calls `on_speed_bar_change(n)` after snap

- [ ] **Step 1: Update `build_motion_section` signature and Scale handling**

In `src/camera/gui_motion.py`, change:

```python
from typing import Any, Callable, Dict, List, Optional
```

Add param `on_speed_bar_change: Optional[Callable[[float], None]] = None` to `build_motion_section`.

Replace `_on_bar` / Scale block so Scale is **not** in `lockable`:

```python
def _on_bar(v: str) -> None:
    n = max(0.05, min(1.0, float(v)))
    n = round(n * 20) / 20
    speed_bar.set(n)
    bar_lbl.set(f"{int(n * 100)}%")
    if on_speed_bar_change is not None:
        on_speed_bar_change(n)

sc = ttk.Scale(bar_row, from_=0.05, to=1.0, orient=tk.HORIZONTAL, command=_on_bar)
sc.set(speed_bar.get())
sc.pack(side=tk.LEFT, fill=tk.X, expand=True)
# do NOT lockable.append(sc)
```

- [ ] **Step 2: Thread callback through SettingsPanel + shell**

`SettingsPanel.__init__`: add `on_speed_bar_change: Optional[Callable[[float], None]] = None` and pass it into `build_motion_section(...)`.

Update hint label text to:

```text
Geometry applies on Start. Exposure/gain, hide-preview, and Speed bar apply live.
```

`build_main_layout` / `gui_shell.py`: add `on_speed_bar_change` kwarg and pass into `SettingsPanel`.

`display_gui` construction site: pass `on_speed_bar_change=self._schedule_live_speed_bar` (stub ok until Task 2 — define method that `pass`es or no-ops if missing).

- [ ] **Step 3: Manual check**

Run: `python -c "from src.camera.gui_motion import build_motion_section; print('ok')"`

Expected: `ok`

Verify file line counts ≤200 for touched files (`wc -l`).

---

### Task 2: Debounced live apply (`set_speed_bar` + `_motion_cfg`)

**Files:**
- Create: `src/camera/live_speed_bar.py`
- Modify: `src/camera/display_gui.py`
- Modify: `src/camera/gui_shell.py` / construction if not done in Task 1

**Interfaces:**
- Consumes: `gui.app` (`_setup_done`, `_motion_cfg`, `controller.set_speed_bar`), `gui._running`, `gui.root`
- Produces:
  - `schedule_live_speed_bar(gui, value: float) -> None`
  - `apply_live_speed_bar(gui, value: float) -> None`

- [ ] **Step 1: Create `src/camera/live_speed_bar.py`**

```python
"""Debounced live Speed bar → robot set_speed_bar + ZigZag _motion_cfg."""

from __future__ import annotations

import threading
from typing import Any

from loguru import logger


def schedule_live_speed_bar(gui: Any, value: float) -> None:
    if not getattr(gui, "_running", False):
        return
    job = getattr(gui, "_speed_bar_job", None)
    if job is not None:
        try:
            gui.root.after_cancel(job)
        except Exception:
            pass
    n = float(value)
    gui._speed_bar_job = gui.root.after(
        150, lambda: apply_live_speed_bar(gui, n)
    )


def apply_live_speed_bar(gui: Any, value: float) -> None:
    gui._speed_bar_job = None
    if not getattr(gui, "_running", False):
        return
    n = max(0.05, min(1.0, float(value)))
    n = round(n * 20) / 20
    app = getattr(gui, "app", None)
    if app is None:
        return
    mcfg = getattr(app, "_motion_cfg", None)
    if isinstance(mcfg, dict):
        mcfg["speed_bar"] = n
    if not getattr(app, "_setup_done", False):
        return

    def _worker() -> None:
        try:
            app.controller.set_speed_bar(n)
            logger.info("Live speed_bar → robot {}", n)
        except Exception as e:
            logger.warning("Live set_speed_bar failed: {}", e)

    threading.Thread(target=_worker, daemon=True).start()
```

- [ ] **Step 2: Wire `display_gui`**

Add:

```python
def _schedule_live_speed_bar(self, value: float) -> None:
    from src.camera.live_speed_bar import schedule_live_speed_bar
    schedule_live_speed_bar(self, value)
```

Pass `on_speed_bar_change=self._schedule_live_speed_bar` into layout/settings (Task 1).

Ensure `self._speed_bar_job = None` in `__init__` if needed.

If `display_gui.py` would exceed 200 lines, keep only the one-liner method and imports already present.

- [ ] **Step 3: Smoke import**

Run: `python -c "from src.camera.live_speed_bar import schedule_live_speed_bar, apply_live_speed_bar; print('ok')"`

Expected: `ok`

---

### Task 3: ZigZag re-read offset each outer loop

**Files:**
- Modify: `src/application/application.py` (`execute_motion_sequence`)

**Interfaces:**
- Consumes: `self._motion_cfg["speed_bar"]`, `self._motion_cfg["offset"]`
- Produces: each outer iteration uses fresh `offset = base_offset * speed_bar` and rebuilt `motions` list

- [ ] **Step 1: Stop baking offset once at start**

Replace the one-shot `speed_bar` / `offset` / `motions` setup with:

- Read static ZigZag params once: `home`, `time_step`, `t1`, `t2`, `gain`, `alpha`, `z`, and **base** `offset_base = float(mcfg.get("offset", MOTION_OFFSET))` (not multiplied).
- At the **start of each `_outer` loop** (before building / using motions):

```python
mcfg = getattr(self, "_motion_cfg", {}) or {}
speed_bar = float(mcfg.get("speed_bar", MOTION_SPEED_BAR))
offset = float(mcfg.get("offset", MOTION_OFFSET)) * speed_bar
motions = [
    [0, offset, offset, 0, 0, 0],
    [offset, offset, 0, 0, 0, 0],
    [offset, 0, -offset, 0, 0, 0],
    [0, -offset, offset, 0, 0, 0],
    [-offset, -offset, 0, 0, 0, 0],
    [-offset, 0, -offset, 0, 0, 0],
]
```

Keep a single info log at routine start; optional debug log when `speed_bar` changes is YAGNI — skip unless useful.

- [ ] **Step 2: Line-count check**

Run: `wc -l src/application/application.py`

Expected: ≤200. If over, extract ZigZag body to `src/application/zigzag.py` with `execute_zigzag(app)` and call it from `execute_motion_sequence`.

---

### Task 4: Hardware / GUI verification

**Files:** none (manual)

- [ ] **Step 1: Restart GUI** (`python run.py`) so code reloads.

- [ ] **Step 2: Sequence path**

Enable robot, routine Sequence/ket, Start. Confirm Speed bar Scale stays enabled; other Motion fields disabled. Drag bar; logs show `Live speed_bar → robot …` (and existing set_speed_bar lines). Robot motion pace changes without Stop.

- [ ] **Step 3: ZigZag path**

Routine ZigZag, Start, drag bar; next outer cycle uses new offset magnitude ( visibly slower/faster `move_speed_l` ).

- [ ] **Step 4: Cameras-only**

Robot disabled, Start, drag bar — no crash; no robot call required.

---

## Spec coverage (self-review)

| Spec requirement | Task |
|------------------|------|
| Scale unlocked while Running | Task 1 |
| Debounced set_speed_bar | Task 2 |
| Update `_motion_cfg["speed_bar"]` | Task 2 |
| ZigZag next-step offset | Task 3 |
| Hint text | Task 1 |
| Multipliers stay locked | Task 1 (unchanged lockable radios) |
| No MoveXB abort | no code path — N/A |

## Placeholder scan

None.

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-24-live-speed-bar.md`. Two execution options:

**1. Subagent-Driven (recommended)** — fresh subagent per task, review between tasks

**2. Inline Execution** — execute tasks in this session with checkpoints

Which approach?
