# Graceful Stop + Immediate Stop

## Problem

GUI Stop sets `stop_requested` and calls `task_stop()`, but the robot worker stays blocked in `wait_move_done` / ZigZag sleeps with no abort path — Stop appears stuck waiting for motion.

## Behavior

| Control | ZigZag | Sequence |
|--------|--------|----------|
| **Stop** (graceful) | `move_speed_l(0…)` immediately → go home → exit | Finish current pass → go home → exit (no new loop pass) |
| **Immediate Stop** | `task_stop()` + abort waits/sleeps → exit in place (no go-home) | Same |

Window close / Start-fail use Immediate-style halt.

## Design

- Dual flags on `RobotApplication`: `stop_requested` (graceful), `immediate_stop` (hard).
- `request_stop()` — set graceful flag only (no `task_stop`).
- `request_immediate_stop()` — both flags + `task_stop()`.
- `wait_move_done` aborts when `immediate_stop` (via `RobotMotion.abort_check`).
- ZigZag sleeps interrupt on either stop flag (so zeros/home can run promptly).
- Sequence mid-pass ignores graceful `stop_requested` (finish pass); aborts only on `immediate_stop`.
- GUI: **Immediate Stop** under Start/Stop.
- Graceful Stop: cameras keep running until the robot worker finishes the cycle/home; **Immediate Stop stays enabled** to escalate; **Start stays disabled** until that finish + camera teardown.
- Immediate Stop (or escalate): `task_stop`, then same watch — Start only after worker exit + cameras down.

## Files

- `src/application/application.py`, `zigzag.py`, `home.py`, `routines.py`
- `src/robot/motion/wait.py`, `base.py`
- `src/camera/gui_shell.py`, `gui_stop.py`, `gui_run.py`, `display_gui.py`
- `src/application/connect_cfg.py` (wire `abort_check`)
