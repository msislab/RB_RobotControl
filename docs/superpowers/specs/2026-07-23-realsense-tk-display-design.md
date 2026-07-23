# RealSense Tk display (demo)

## Goal
Live RealSense preview in Tkinter with Start/Stop and view mode selected only at Start. Camera runs alongside robot motion on a worker thread. No image saving.

## View modes
- `rgb` — color only
- `rgb_depth` — color + depth (colormap)
- `rgb_depth_ir` — color + depth + IR1 + IR2

## Lifecycle
1. App opens Tk GUI (camera and robot idle).
2. **Start**: lock view radios → start pipeline for selected mode → show frames → run motion on background thread.
3. **Stop**: request robot stop → close camera → unlock radios.
4. Window close: full shutdown.

## Modules
- `src/camera/realsense_camera.py` — thin pyrealsense2 capture
- `src/camera/display_gui.py` — Tk controls + image panels
- `config.yaml` `camera:` section — defaults
- `src/main.py` — launch GUI

## Out of scope
Saving, OTF exposure, stereo calibration, USB reset helpers.
