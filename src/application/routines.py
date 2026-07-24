"""Selectable robot motion routines (ZigZag / sequence file)."""

from __future__ import annotations

from typing import Any, List, Tuple

import numpy as np
from loguru import logger

from src.config.ket_store import load_ket, resolve_path
from src.config.loader import (
    XB_JOINT_ACCELERATION,
    XB_JOINT_SPEED,
    XB_LINEAR_ACCELERATION,
    XB_LINEAR_SPEED,
)
from src.utils.color import green, yellow

ROUTINE_ZIGZAG = "zigzag"
ROUTINE_KET = "ket"  # play selected sequences/<name>.yaml
ROUTINES = (ROUTINE_ZIGZAG, ROUTINE_KET)


def normalize_routine(name: Any) -> str:
    key = str(name or ROUTINE_ZIGZAG).strip().lower()
    return key if key in ROUTINES else ROUTINE_ZIGZAG


def _load_steps(sequence_name: str) -> List[Tuple[str, np.ndarray]]:
    """Return ordered (mode, pose) steps; skip bad/missing points."""
    data = load_ket(resolve_path(sequence_name))
    points = dict(data["points"])
    steps: List[Tuple[str, np.ndarray]] = []
    for name in data["sequence"]:
        pt = points.get(name)
        if not pt:
            logger.warning(yellow(f"Skip missing point {name!r}"))
            continue
        mode = str(pt.get("mode", "tcp")).lower()
        pose = np.array(pt.get("pose") or [], dtype=float)
        if pose.shape != (6,):
            logger.warning(yellow(f"Skip bad pose {name!r}"))
            continue
        steps.append(("joint" if mode == "joint" else "tcp", pose))
    return steps


def _seq_speeds(mcfg: dict) -> dict:
    """Base Motion speeds for point-by-point sequence (robot multipliers separate)."""
    return {
        "joint_speed": float(mcfg.get("joint_speed", 180.0)),
        "joint_acc": float(mcfg.get("joint_acc", 180.0)),
        "linear_speed": float(mcfg.get("linear_speed", 1000.0)),
        "linear_acc": float(mcfg.get("linear_acc", 1000.0)),
        "blend": float(mcfg.get("xb_blend_distance", 100.0)),
    }


def _xb_speeds(mcfg: dict) -> dict:
    """MoveXB add speeds from speed.xb (joint %; linear mm/s). Blend from motion cfg."""
    return {
        "joint_speed": float(XB_JOINT_SPEED),
        "joint_acc": float(XB_JOINT_ACCELERATION),
        "linear_speed": float(XB_LINEAR_SPEED),
        "linear_acc": float(XB_LINEAR_ACCELERATION),
        "blend": float(mcfg.get("xb_blend_distance", 100.0)),
    }


def _play_sequence_once(app: Any, sequence_name: str, *, merge: bool) -> bool:
    """Play one pass (point-by-point or one MoveXB). False if stopped mid-way."""
    steps = _load_steps(sequence_name)
    if not steps:
        logger.warning(yellow(f"Sequence {sequence_name!r} empty — nothing to run"))
        return True
    path = resolve_path(sequence_name)
    mcfg = getattr(app, "_motion_cfg", {}) or {}
    spd = _seq_speeds(mcfg)
    logger.info(
        green(
            f"Sequence {sequence_name!r}: {len(steps)} step(s) ← {path} "
            f"(robot spd_mult={mcfg.get('speed_multiplier', 1)} "
            f"acc_mult={mcfg.get('acceleration_multiplier', 1)})"
        )
    )
    if merge:
        if app.stop_requested:
            return False
        xb = _xb_speeds(mcfg)
        logger.info(
            green(
                f"MoveXB adds: joint {xb['joint_speed']}%/{xb['joint_acc']}% "
                f"linear {xb['linear_speed']} mm/s / {xb['linear_acc']} mm/s² "
                f"blend={xb['blend']}"
            )
        )
        app.controller.move_xb(
            steps,
            linear_speed=xb["linear_speed"],
            linear_acc=xb["linear_acc"],
            joint_speed=xb["joint_speed"],
            joint_acc=xb["joint_acc"],
            blend_distance=xb["blend"],
        )
        return not app.stop_requested
    for mode, pose in steps:
        if app.stop_requested:
            return False
        logger.info(green(f"→ ({mode}) {pose}"))
        if mode == "joint":
            app.controller.move_j(
                pose, speed=spd["joint_speed"], acc=spd["joint_acc"]
            )
        else:
            app.controller.move_to_point(
                pose, speed=spd["linear_speed"], acc=spd["linear_acc"]
            )
    return not app.stop_requested


def execute_ket_sequence(
    app: Any,
    sequence_name: str = "ket",
    *,
    loop: bool = False,
    merge: bool = False,
) -> None:
    """Play sequences/<name>.yaml; optional MoveXB merge and/or loop until Stop."""
    if not app.running and not app.stop_requested:
        raise RuntimeError("Application not set up. Call setup() first.")
    app.running = True
    app.stop_requested = False
    pass_n = 0
    while True:
        if app.stop_requested:
            break
        pass_n += 1
        if loop:
            logger.info(green(f"Sequence loop pass {pass_n} merge={bool(merge)}"))
        finished = _play_sequence_once(app, sequence_name, merge=bool(merge))
        if not loop or not finished or app.stop_requested:
            break
    logger.info(
        green(
            f"Sequence {sequence_name!r} ended"
            + (f" after {pass_n} pass(es)" if loop else "")
        )
    )


def run_routine(
    app: Any,
    name: Any,
    sequence_name: Any = "ket",
    *,
    loop: bool = False,
    merge: bool = False,
) -> None:
    """Dispatch ZigZag or selected sequence file."""
    routine = normalize_routine(name)
    logger.info(
        green(f"Running robot routine: {routine} loop={bool(loop)} merge={bool(merge)}")
    )
    if routine == ROUTINE_KET:
        execute_ket_sequence(
            app,
            str(sequence_name or "ket").strip() or "ket",
            loop=bool(loop),
            merge=bool(merge),
        )
    else:
        app.execute_motion_sequence()
