# Plan: Robot connect at launch (option C)

Spec: `docs/superpowers/specs/2026-07-23-robot-connect-at-launch-design.md`

## Files
- `src/application/application.py` — `connect_with_settings` (idle connected); `setup_with_settings` uses it then `running=True`
- `src/camera/gui_connect.py` — threaded connect worker + launch auto-connect
- `src/camera/gui_robot_panel.py` — Connect button
- `src/camera/display_gui.py` — schedule launch connect; wire Connect
- `src/camera/gui_run.py` — fix missing `_refresh_status`; Stop keeps connection (already)

## Tasks
1. Application connect-without-routine
2. gui_connect helpers
3. Panel Connect button + status sync
4. Wire display_gui launch + callback
5. Smoke import / line counts
