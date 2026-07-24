# XB Max Speed Config Implementation Plan

> **For agentic workers:** Execute task-by-task. Steps use checkbox syntax.

**Goal:** Merge movements (MoveXB) always add points using `speed.xb` max speed/acc from config.

**Architecture:** Annotate `speed.yaml` with min/max; expose `XB_*` loader constants; merge path in `routines.py` uses those instead of Motion panel; align `xb.py` defaults.

**Tech Stack:** Python, rbpodo MoveXB, YAML config

## Global Constraints

- `move_xb_j_add` speed/acc are % (0–100); `move_xb_p_add` are mm/s and mm/s²
- Do not change Motion panel behavior for non-merge
- Preserve existing user-edited `joint`/`cartesian`/`multiplier` values in `speed.yaml`
- Application source ≤200 lines per file

---

### Task 1: Config + loader

- [x] Update `src/config/speed.yaml`: min/max comments on joint/cartesian; add `xb:` block
- [x] Export `XB_JOINT_SPEED`, `XB_JOINT_ACCELERATION`, `XB_LINEAR_SPEED`, `XB_LINEAR_ACCELERATION` from `loader.py` (+ `__init__.py` if needed)

### Task 2: Runtime wiring

- [x] `routines._play_sequence_once(merge=True)` pass XB constants into `move_xb`
- [x] `xb.py` defaults → 100 / 100 / 1000 / 1000
- [x] Log XB units on merge start for clarity

### Task 3: Verify

- [x] Import check: loader exposes XB_* and YAML parses
- [x] Update `memory.md`
