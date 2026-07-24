# RobotControl_RB

A Python-based robot control system for RB (Robot Control) robots using the `rbpodo` library. This repository provides a structured framework for controlling robot motion, including point-to-point movement, velocity-based control, servo control, and Imaginary Conveyor (ICV) operations.

## Features

- **Multiple Motion Types**: Point-to-point, servo control, speed control, and jogging
- **Cartesian and Joint Space Control**: Support for both Cartesian and joint space operations
- **ICV Support**: Imaginary Conveyor functionality for continuous motion
- **Collision Detection**: Built-in collision detection and safety checks
- **Configurable Settings**: YAML-based configuration for robot parameters
- **Structured Architecture**: Modular design with clear separation of concerns

## Project Structure

```
RobotControl_RB/
├── src/
│   ├── application/          # Main application orchestration
│   ├── config/               # Configuration management
│   ├── robot/
│   │   ├── connection/       # Robot connection management
│   │   ├── controller/       # High-level robot controller
│   │   ├── motion/           # Motion control implementations
│   │   ├── settings/         # Robot settings management
│   │   └── data/             # Data collection
│   └── utils/                # Utility functions
├── run.py                    # Entry point
└── README.md
```

## Installation

1. Ensure you have Python 3.x installed
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

   `rbpodo>=0.16.14` is required for MoveXB (`move_xb_*`).
## Configuration

Edit the per-component YAML files under `src/config/`:

| File | Contents |
|------|----------|
| `robot.yaml` | IP, enable, routine, operation mode, collision |
| `speed.yaml` | Joint / cartesian speed & accel |
| `motion.yaml` | ZigZag / GUI motion parameters |
| `camera.yaml` | RealSense |
| `omron.yaml` | Omron GigE |
| `sequences/<name>.yaml` | Taught sequence files (default `ket`) |
| `logger.yaml` | Logging |

`robot_sequence` in `robot.yaml` picks which `sequences/<name>.yaml` runs when routine is Sequence. Create more files from the robot-control menu (**New**).

## Usage

### Basic Usage

Run the application:
```bash
python run.py
```

### Programmatic Usage

```python
from src.application.application import RobotApplication

# Initialize application
app = RobotApplication("192.168.2.101")
app.setup()

# Execute motion sequence
app.execute_motion_sequence()

# Or execute ICV sequence
# app.execute_icv_sequence()

# Cleanup
app.shutdown()
```

## Motion Control

The system supports various motion control methods:

- **Point-to-Point**: `move_to_point()` - Move to a specific TCP position
- **Servo Control**: `move_servo_l()` / `move_servo_j()` - High-frequency position updates
- **Speed Control**: `move_speed_l()` / `move_speed_j()` - Velocity-based continuous motion
- **Jogging**: `jog_robot_l()` / `jog_robot_j()` - Manual jogging control

---

## `move_speed_l()` Input Parameters

```python
move_speed_l(pnt[dx, dy, dz, drx, dry, drz], t1, t2, gain, alpha)
```

`move_speed_l()` commands Cartesian velocity-based motion of the TCP.

Unlike point-to-point motion, it enables continuous, non-stop movement and allows smooth blending with other motions (e.g., ICV, vision correction, jogging).

⸻

### 1. dx, dy, dz — Linear Velocity (mm/s)

Defines TCP linear velocity along the Cartesian axes.

- **Unit**: mm/s
- **Positive/negative values**: Indicate direction

| Parameter | Description |
|-----------|-------------|
| dx | Velocity along X-axis |
| dy | Velocity along Y-axis |
| dz | Velocity along Z-axis |

**Notes:**
- These values represent velocity, not displacement.
- Motion continues while the command is active or repeatedly updated.

⸻

### 2. drx, dry, drz — Angular Velocity (deg/s)

Defines TCP rotational velocity using ZYX Euler angles.

- **Unit**: deg/s

| Parameter | Description |
|-----------|-------------|
| drx | Rotation speed about X-axis |
| dry | Rotation speed about Y-axis |
| drz | Rotation speed about Z-axis |

⸻

### 3. t1 — Velocity Ramp-Up Time (seconds)

Time required to reach the target velocity. Controls acceleration smoothness.

- **Constraint**: `t1 ≥ 0.002`

| Value Range | Effect |
|-------------|--------|
| Very small | Fast acceleration, sharp motion |
| Larger | Smooth, gradual acceleration |

⸻

### 4. t2 — Velocity Hold Time (seconds)

Duration for which the commanded velocity is maintained after reaching it.

- **Constraint**: `0.02 < t2 < 0.2`

| Value | Effect |
|-------|--------|
| Small | Short velocity pulse |
| Larger | Stable continuous motion |

**Note:** For continuous motion, this command is typically reissued periodically in a control loop.

⸻

### 5. gain — Velocity Gain

Scales the commanded velocity. Must be greater than zero.

| Gain | Effect |
|------|--------|
| < 1.0 | Reduced motion speed |
| 1.0 | Nominal speed |
| > 1.0 | More aggressive response |

⸻

### 6. alpha — Low-Pass Filter Gain

Controls motion smoothness via low-pass filtering.

- **Range**: `0 < alpha < 1`

| Alpha Value | Motion Behavior |
|-------------|-----------------|
| Small | Very smooth, soft response |
| Medium | Balanced smoothness and responsiveness |
| Large | Sharp, responsive, less filtered |

Lower values result in smoother motion, especially useful when blending with other commands.

⸻

### Practical Notes

- `move_speed_l()` is suitable for continuous motion, such as:
  - Trajectory blending
  - Vision-based correction
  - Imaginary conveyor operation
- It is recommended to update the command at a fixed rate (e.g., 10–50 Hz) for stable motion.
- To stop smoothly, send zero velocities with a non-zero t1 and a low alpha:

```python
move_speed_l([0, 0, 0, 0, 0, 0], t1, t2, gain, alpha)
```

⸻

### Example Usage

```python
import numpy as np
from src.robot.controller import RobotController

controller = RobotController("192.168.2.101")
controller.connect()
controller.initialize()

# Move in X direction at 50 mm/s
cartesian_speeds = np.array([50.0, 0.0, 0.0, 0.0, 0.0, 0.0])
controller.move_speed_l(
    cartesian_speeds,
    t1=0.1,      # 0.1s ramp-up time
    t2=0.05,     # 0.05s hold time
    gain=1.0,    # Full speed
    alpha=0.5    # Medium smoothness
)
```

## License

[Specify your license here]

## Contributing

[Contributing guidelines if applicable]
```

This README includes:
1. Project overview and features
2. Project structure
3. Installation instructions
4. Configuration guide
5. Usage examples