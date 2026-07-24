"""Quiet TCP/joint reads + status-line formatting (no INFO spam)."""

from __future__ import annotations

from typing import Any, Optional, Sequence, Tuple

import numpy as np


def robot_connected(app: Any) -> bool:
    return bool(getattr(app, "_setup_done", False))


def peek_pose(app: Any) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """Return (tcp, joints) from data_collector when connected; else (None, None)."""
    if not robot_connected(app):
        return None, None
    try:
        data = app.controller.connection.data_collector.data
        tcp = np.round(np.asarray(data.tcp_pos, dtype=float), 2)
        joints = np.round(np.asarray(data.jnt_ref, dtype=float), 2)
        return tcp, joints
    except Exception:
        return None, None


def peek_collision(app: Any) -> bool:
    """True if external or self collision flag is set."""
    if not robot_connected(app):
        return False
    try:
        ctrl = app.controller
        return bool(ctrl.has_external_collision() or ctrl.has_self_collision())
    except Exception:
        return False


def _fmt_vec(prefix: str, values: Optional[Sequence[float]]) -> str:
    if values is None:
        return f"{prefix}=—"
    return f"{prefix}[{', '.join(f'{float(v):.2f}' for v in values)}]"


def format_run_status(
    *,
    rs_on: bool,
    omron_n: int,
    tcp: Optional[Sequence[float]],
    joints: Optional[Sequence[float]],
) -> str:
    return (
        f"Running · {_fmt_vec('TCP', tcp)} · {_fmt_vec('J', joints)} · "
        f"rs={rs_on} · omron={omron_n}"
    )
