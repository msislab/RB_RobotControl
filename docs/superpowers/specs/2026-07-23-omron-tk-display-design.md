# Omron Tk display + live exposure/gain

## Goal
Live Omron (StApi/stapipy) RGB preview alongside RealSense in one shared grid.
Enable/disable each backend. Live exposure/gain while running. Omron IP auto-assign.

## Decisions
- Omron: RGB only, freerun (`TriggerMode=Off`)
- Discover and connect all available Omron devices when enabled
- Shared W/H with RealSense (applied at Start)
- Exposure/gain editable while running (debounced apply)
- IP assignment + device open/`start_acquisition` at **process start** (`prepare_omron_network` + `open_omron_devices_at_startup`); GUI Start only attaches to the pool

## Modules
- `src/camera/omron_camera.py` — connect/stream/exposure
- `src/camera/omron_net.py` — IP pool assignment
- `src/camera/omron_nodes.py` — GenICam nodemap helpers
- RealSense + GUI settings/display updates

## Out of scope
Software-trigger inspection pipeline, image save, Omron depth/IR.
