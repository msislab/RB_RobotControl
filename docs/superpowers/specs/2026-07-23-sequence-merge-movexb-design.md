# Merge movements via MoveXB (approved)

## Dependency
- `rbpodo>=0.16.14` (provides `move_xb_clear` / `move_xb_p_add` / `move_xb_j_add` / `move_xb_run`)
- Pinned in `requirements.txt`

## UI
- Checkbox **Merge movements (MoveXB)** (`robot_sequence_merge`)

## Runtime
- Clear XB buffer → add each sequence point (tcp→p_add, joint→j_add, blend distance 100 / last 0) → `move_xb_run(Position)` → wait finished
- Works with Loop (re-pack each pass)
- Pattern matches AIRobot_Framework `_move_advanced(..., method='XB')`
