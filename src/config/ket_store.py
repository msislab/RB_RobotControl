"""Load/save taught sequences under src/config/sequences/<name>.yaml."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

import yaml
from loguru import logger

from src.utils.color import green, yellow

SEQUENCES_DIR = Path(__file__).parent / "sequences"
PathLike = Union[str, Path]


def sequences_dir() -> Path:
    SEQUENCES_DIR.mkdir(parents=True, exist_ok=True)
    return SEQUENCES_DIR


def list_sequences() -> List[str]:
    root = sequences_dir()
    return sorted(p.stem for p in root.glob("*.yaml"))


def _safe_stem(name: str) -> str:
    stem = str(name).strip()
    if not stem or any(c in stem for c in "/\\"):
        raise ValueError(f"Invalid sequence name: {name!r}")
    return stem


def sequence_path(name: str) -> Path:
    return sequences_dir() / f"{_safe_stem(name)}.yaml"


def resolve_path(path_or_name: Optional[PathLike] = None) -> Path:
    if path_or_name is None:
        return sequence_path("ket")
    if isinstance(path_or_name, Path):
        return path_or_name
    text = str(path_or_name)
    if text.endswith(".yaml") or "/" in text or "\\" in text:
        return Path(text)
    return sequence_path(text)


def config_path() -> Path:
    """Default sequence file (ket)."""
    return sequence_path("ket")


def load_ket(path_or_name: Optional[PathLike] = None) -> Dict[str, Any]:
    p = resolve_path(path_or_name)
    if not p.exists():
        return {"points": {}, "sequence": []}
    with open(p, "r", encoding="utf-8") as f:
        ket = yaml.safe_load(f) or {}
    if not isinstance(ket, dict):
        ket = {}
    if "points" not in ket and "ket" in ket and isinstance(ket["ket"], dict):
        ket = ket["ket"]
    points = dict(ket.get("points") or {})
    sequence = [str(n) for n in (ket.get("sequence") or [])]
    return {"points": points, "sequence": sequence}


def save_ket(
    points: Dict[str, Any],
    sequence: List[str],
    path_or_name: Optional[PathLike] = None,
) -> None:
    p = resolve_path(path_or_name)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {"points": points, "sequence": sequence}
    with open(p, "w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, default_flow_style=False, sort_keys=False)
    logger.info(green(f"Sequence saved → {p} ({len(sequence)} steps, {len(points)} points)"))


def ensure_sequence(name: str) -> Path:
    """Create empty sequence file if missing; return path."""
    p = sequence_path(name)
    if not p.exists():
        save_ket({}, [], p)
        logger.info(yellow(f"Created sequence {name!r}"))
    return p


def record_point(
    name: str,
    mode: str,
    pose: Sequence[float],
    path_or_name: Optional[PathLike] = None,
) -> Dict[str, Any]:
    key = str(name).strip()
    if not key:
        raise ValueError("Point name is empty")
    m = "joint" if str(mode).lower() == "joint" else "tcp"
    vals = [float(v) for v in pose]
    if len(vals) != 6:
        raise ValueError(f"Pose must have 6 values, got {len(vals)}")
    data = load_ket(path_or_name)
    is_new = key not in data["points"]
    data["points"][key] = {"mode": m, "pose": vals}
    if is_new:
        data["sequence"].append(key)
    save_ket(data["points"], data["sequence"], path_or_name)
    logger.info(yellow(f"Record {key!r} mode={m} new={is_new}"))
    return data


def delete_point(name: str, path_or_name: Optional[PathLike] = None) -> Dict[str, Any]:
    key = str(name).strip()
    if not key:
        raise ValueError("Point name is empty")
    data = load_ket(path_or_name)
    if key not in data["points"] and key not in data["sequence"]:
        raise KeyError(f"Unknown point: {key}")
    data["points"].pop(key, None)
    data["sequence"] = [n for n in data["sequence"] if n != key]
    save_ket(data["points"], data["sequence"], path_or_name)
    logger.info(yellow(f"Deleted point {key!r}"))
    return data
