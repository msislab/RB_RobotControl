# MoveXB adds at config max speed (approved)

## Goal
When **Merge movements** runs MoveXB, every `move_xb_j_add` / `move_xb_p_add` uses dedicated max speed/acc from `speed.yaml` (`speed.xb`), not the Motion panel joint/linear fields.

## Config (`src/config/speed.yaml`)

Annotate existing `joint` / `cartesian` entries with min/max comments (hardware where known).

Add:

```yaml
xb:  # Merge movements (MoveXB) only — always used for *_add
  joint_speed: 100.0           # % — min 0, max 100 (rbpodo move_xb_j_add)
  joint_acceleration: 100.0    # % — min 0, max 100
  linear_speed: 1000.0         # mm/s — min 0, max 1000 (RB tool max 1 m/s)
  linear_acceleration: 1000.0  # mm/s² — min 0; no published hardware max (controller err 324 if out of range)
```

Existing limits (comments only; values unchanged unless already edited by user):

- `joint.speed`: deg/s — min 0, max 180 (RB joint max)
- `joint.acceleration`: deg/s² — min 0; no published hardware max
- `cartesian.linear_speed`: mm/s — min 0, max 1000
- `cartesian.linear_acceleration`: mm/s² — min 0; no published hardware max

## Runtime

- `_play_sequence_once(..., merge=True)` loads `speed.xb` (via loader constants or `app` config) and passes those four values into `controller.move_xb(...)`.
- Non-merge sequence / ZigZag: unchanged — Motion panel + `speed.joint` / `speed.cartesian` as today.
- Robot `set_speed_bar` / `set_speed_multiplier` / `set_acc_multiplier` still apply on top; do not bypass them.
- `run_move_xb` defaults should align with `speed.xb` maxes (100 / 100 / 1000 / 1000) so accidental callers without kwargs are not slow.

## Units (explicit)

| API | Speed unit | Acc unit |
|-----|------------|----------|
| `move_xb_j_add` | % (0–100) | % (0–100) |
| `move_xb_p_add` | mm/s | mm/s² |
| `move_j` | deg/s | deg/s² |
| `move_l` | mm/s | mm/s² |

Do **not** pass Motion-panel deg/s values into `move_xb_j_add`.

## Out of scope

- Changing GUI Motion fields for XB
- Changing blend distance policy
- Safety slide-bar / speed_bar UI redesign

## Success

- Merge path logs / args show XB joint % and linear mm/s from `speed.xb`
- Editing `speed.xb` changes MoveXB add speeds without touching Motion panel
- Point-by-point sequence still uses Motion speeds
