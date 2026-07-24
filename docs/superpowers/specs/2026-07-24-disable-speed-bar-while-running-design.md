# Disable Speed bar while Running (approved)

Supersedes live-while-running behavior in
`2026-07-24-live-speed-bar-design.md`.

## Goal

Avoid wedging the Cobot command channel: never call `set_speed_bar` from the
GUI while a routine is Running. Speed bar is editable only when Stopped and
applies on Start/connect.

## Behavior

- On Start, `set_locked(True)` disables the Speed bar Scale with other Motion fields.
- On Stop, Scale unlocks again.
- No live `set_speed_bar` / `live_speed_bar` apply while Running.
- Start/connect still push `speed_bar` from settings as today.
- Hint: Geometry / exposure-gain / hide-preview notes; Speed bar applies on Start.

## Out of scope

- Mid-run live speed for Sequence or ZigZag
- Robot RPC serialization layer

## Success

- Dragging Speed bar is impossible while Running.
- Sequence/MoveXB loops are not interrupted by concurrent `set_speed_bar`.
