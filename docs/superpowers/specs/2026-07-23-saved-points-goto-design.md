# Saved points list + Go to (approved)

## Goal
In robot controls, show taught points for the active sequence and move to a selected point.

## UI
- LabelFrame **Saved points** (list in sequence order: `name (tcp|joint)`).
- **Go to point** — worker thread; tcp→`move_to_point`, joint→`move_j` (wait until done).
- **Fill into Move** — copy pose into Manual fields + mode.
- Refresh on sequence change / Record / Delete / panel open.

## Out of scope
- Reorder/edit in list (use teach Record/Delete).
