# Robot control menu + KET teach (YAML)

## Goal
Swap the left settings pane for a robot control menu (Back returns to main). Show collision status with Resume. Manual Home / Move (TCP or Joint). Teach named KET points into `ket.yaml` and play them when routine=KET.

## Decisions (approved)
- **Nav:** Replace settings scroll only; Start/Stop stay. Open robot controls ↔ Back to main.
- **Availability:** Panel always viewable; Home / Move / Resume / Record require robot connected (`_setup_done`).
- **KET store:** Named map + ordered `ket.sequence` in YAML (not SQL).
- **TCP vs Joint:** Per Move and per Record; each point stores `mode: tcp|joint` + 6 values.

## UI — Robot control panel
| Control | Behavior |
|---------|----------|
| Status | `Normal` / `Collision` from data_collector collision flags (~5 Hz while panel visible) |
| Resume | Enabled only when Collision + connected → `task_resume(collision=True)` |
| Go Home | Connected → `move_to_point(home)` from motion home settings |
| Move | Mode TCP\|Joint + 6 entries + Move → TCP: `move_to_point`; Joint: `move_servo_j` |
| KET teach | Name + mode + Record → upsert `ket.points[name]`; append to `ket.sequence` if new |
| KET delete | Delete selected/named point from `ket.points` and remove from `ket.sequence` |
| Back | Restore SettingsPanel |

## YAML shape
```yaml
ket:
  points:
    pick:
      mode: tcp    # or joint
      pose: [x, y, z, rx, ry, rz]   # joints if mode=joint
  sequence:
    - pick
    - place
```

## Runtime
- **ZigZag:** unchanged `execute_motion_sequence`.
- **KET Start:** walk `ket.sequence`; for each name load point; TCP → `move_to_point`, Joint → `move_servo_j`; honor `stop_requested`.
- YAML write: dump `ket.yaml` only (points + sequence); reload after Record/Delete.

## Modules (≤200 lines each)
- `gui_robot_panel.py` — robot control widgets
- `gui_shell` / `display_gui` — view swap Open/Back
- `ket_store.py` — load/save points + sequence in YAML
- `routines.py` — real `execute_ket_sequence` using ket_store
- Collision peek helper (quiet, no INFO spam)

## Out of scope
- Drag-reorder of sequence in GUI (order = record order; delete removes from sequence)
- SQLite or other DBs
