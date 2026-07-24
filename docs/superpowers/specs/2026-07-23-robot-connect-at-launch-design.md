# Robot connect at launch + Connect button (option C)

## Goal
Auto-connect the robot when the app starts **only if Enable Robot is on**. Otherwise (or after a failed connect), the robot-control panel exposes **Connect to robot** so the user can connect without pressing Start. Manual teach / Home / Move work once `_setup_done`.

## Decisions (approved)
- **Option C / Approach 1:** Auto-connect at GUI launch iff Enable Robot checked (defaults from settings / `robot.yaml`).
- **Connect button:** In robot-control panel when disconnected; uses current settings IP + mode (+ speeds).
- **Stop keeps connection:** Stop ends cameras + motion loop; disconnect only on window close / `shutdown`.
- **Enable toggle after launch:** Turning Enable on does not auto-connect; user presses Connect (or Start with robot enabled). Turning Enable off does not disconnect.
- **No Disconnect button** in this pass.

## Launch
1. GUI builds with settings defaults (`robot_enabled`, `robot_ip`, `operation_mode`, speeds).
2. If `robot_enabled`: start a **background worker** that calls connect + initialize + apply settings (same path as Start’s robot setup, without running a routine). Must not block Tk.
3. On success: `_setup_done = True`; pose/collision status become live.
4. On failure: log + status line; panel shows Connect enabled.

## Robot control panel
| Control | Behavior |
|---------|----------|
| Connect to robot | Visible/enabled when not connected. Reads current settings → connect/init/apply. Worker thread; disable button while connecting. |
| When connected | Button disabled or label **Connected**. |
| Home / Move / Resume / Record / Sequence teach | Unchanged: require connected (`_setup_done`). |
| Status | Disconnected / Normal / Collision as today. |

## Start / Stop
- **Start + Enable Robot:** If already connected and IP unchanged → apply settings, collision resume, run routine. If IP changed or not connected → reconnect then run routine.
- **Start + Enable off:** Cameras only (unchanged).
- **Stop:** Stop cameras + `request_stop` on motion; **do not** tear down robot connection.
- **Window close:** Existing Omron + `app.shutdown` disconnect.

## Modules (≤200 lines each)
- `application.py` — keep/extend `setup_with_settings`; ensure connect-without-routine is safe (no `running` motion until Start, or `running` only for data path — prefer: `_setup_done` + connected without setting motion `running` until Start/routine).
- `gui_robot_panel.py` / small helper — Connect button + connecting state.
- `display_gui.py` / `gui_run.py` / `main` — schedule auto-connect after GUI ready; wire Connect callback to settings.values().
- `gui_pose.robot_connected` — stays `_setup_done`.

## Out of scope
- Explicit Disconnect button
- Auto-connect when user checks Enable Robot after launch
- Changing default robot IP / collision / speeds in YAML
