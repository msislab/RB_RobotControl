# Global Speed bar (ZigZag + Sequence)

## Goal

GUI Speed bar slider drives the robot’s global `set_speed_bar` (0–1) for both ZigZag and Sequence. ZigZag keeps its existing software `offset *= speed_bar` scaling.

## Behavior

- On connect/start (`connect_with_settings`), call `set_speed_bar(cfg["speed_bar"])`, falling back to YAML `default_speed_bar`.
- Sequence / MoveXB: affected only via robot global bar (plus existing Speed/Acc multipliers).
- ZigZag: robot global bar **and** unchanged `offset * speed_bar` for `move_speed_l`.
- Label: “Speed bar (global; also scales ZigZag)”.

## Out of scope

- Config YAML defaults
- Removing ZigZag offset scaling
- Live bar updates mid-motion (still applied at connect/start)
