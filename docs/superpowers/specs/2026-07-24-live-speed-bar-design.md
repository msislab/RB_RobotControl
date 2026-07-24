# Live Speed bar while Running — SUPERSEDED

**Superseded by** `2026-07-24-disable-speed-bar-while-running-design.md`.
Live `set_speed_bar` during Running wedged the Cobot command channel mid-MoveXB;
Speed bar is now locked while Running and applies on Start only.

## Goal (historical)

While the GUI is **Running**, the Motion **Speed bar** slider stays usable and:

1. Pushes the robot’s global `set_speed_bar` (0–1) in near real time, and  
2. Updates ZigZag’s software `offset * speed_bar` on the next ZigZag loop step.

Other Motion fields stay locked. Speed/Acc multipliers are not live.

## Behavior

- On Start, `set_locked(True)` disables lockable widgets **except** the Speed bar Scale (label stays readable).
- Dragging the bar still snaps to 5% steps (0.05–1.0), same as today.
- When Running **and** the robot is connected (`_setup_done`), schedule a **debounced** (~150 ms) apply on a short background thread (do not block Tk):
  - `controller.set_speed_bar(n)`
  - write `n` into `app._motion_cfg["speed_bar"]` (so ZigZag re-reads it)
- If robot is disabled / not connected, slider still updates the Tk var (and `_motion_cfg` if setup exists) for the next Start; skip the robot call when not connected.
- **Sequence / MoveXB:** affected via the robot global bar only (plus multipliers set at Start).
- **ZigZag:** each outer/inner step (or each `move_speed_l` call site) recomputes  
  `offset = cfg_offset * current_speed_bar` from `_motion_cfg`, so a live bar change takes effect on the **next** ZigZag motion command — not mid-command.
- Hint text: Speed bar applies live while running (robot global + ZigZag offset).

## Approaches considered

1. **Unlock Speed bar + debounce → `set_speed_bar` + update `_motion_cfg`** (chosen).
2. Separate always-on Speed bar control — more UI churn, same effect.
3. Poll only from robot worker — couples motion loops; poorer for long MoveXB calls.

## Out of scope

- Live Speed/Acc multiplier radios
- Config YAML default changes
- Changing `set_speed_bar` units / rbpodo API
- Aborting / rewriting an in-flight MoveXB when the bar moves

## Success

- With Sequence/Merge Running, dragging Speed bar changes robot speed without Stop/Start.
- With ZigZag Running, dragging Speed bar changes the next `move_speed_l` offset magnitude without Stop/Start.
- Other Motion entries remain disabled while Running.
