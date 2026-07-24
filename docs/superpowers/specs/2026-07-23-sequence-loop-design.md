# Sequence loop until Stop (approved)

## UI
- Main settings checkbox **Loop sequence** (`robot_sequence_loop`).
- Applies when routine = Sequence; ZigZag ignores.

## Runtime
- Loop on: repeat selected sequence until Stop (`stop_requested`).
- Reload YAML each pass.
- Loop off: one pass.
