"""GenICam nodemap helpers for Omron/StApi."""

from __future__ import annotations

from typing import Any, Optional, Tuple

from loguru import logger

_ALIASES = {"Gain": "GainRaw", "ExposureTime": "ExposureTimeRaw"}


def set_enumeration(st: Any, nodemap: Any, key: str, value: Any) -> None:
    node = nodemap.get_node(key)
    if node is None:
        logger.warning("Node {} not found", key)
        return
    enum_node = st.PyIEnumeration(node)
    try:
        entry = enum_node[str(value)]
        enum_node.set_entry_value(st.PyIEnumEntry(entry))
        return
    except Exception:
        pass
    try:
        enum_node.set_int_value(int(value))
    except Exception:
        logger.exception("Failed to set enumeration {}={}", key, value)


def _resolve_node(nodemap: Any, key: str) -> Tuple[Optional[Any], str]:
    node = nodemap.get_node(key)
    if node is None:
        alias = _ALIASES.get(key)
        if alias:
            node = nodemap.get_node(alias)
            if node is not None:
                return node, alias
    return node, key


def set_numeric(st: Any, nodemap: Any, key: str, value: Any) -> None:
    node, key = _resolve_node(nodemap, key)
    if node is None:
        logger.warning("Numeric node {} not found", key)
        return
    try:
        st.PyIFloat(node).value = float(value)
        return
    except Exception:
        pass
    try:
        st.PyIInteger(node).value = int(float(value))
    except Exception:
        logger.exception("Failed to set numeric {}={}", key, value)


def numeric_range(st: Any, nodemap: Any, key: str) -> Optional[Tuple[float, float]]:
    """Return (min, max) for a GenICam float/int node, or None."""
    node, key = _resolve_node(nodemap, key)
    if node is None:
        return None
    try:
        n = st.PyIFloat(node)
        return float(n.min), float(n.max)
    except Exception:
        pass
    try:
        n = st.PyIInteger(node)
        return float(n.min), float(n.max)
    except Exception:
        logger.exception("Failed to read range for {}", key)
        return None


def _int_node(st: Any, nodemap: Any, key: str) -> Optional[Any]:
    node = nodemap.get_node(key)
    if node is None:
        return None
    try:
        return st.PyIInteger(node)
    except Exception:
        return None


def set_max_roi(st: Any, nodemap: Any) -> Optional[tuple]:
    """Offset→min, Width/Height→max. Returns (w, h) or None."""
    for key in ("OffsetX", "OffsetY"):
        inode = _int_node(st, nodemap, key)
        if inode is None:
            continue
        try:
            inode.value = int(inode.min)
        except Exception:
            logger.exception("Failed to set {} to min", key)
    w_node = _int_node(st, nodemap, "Width")
    h_node = _int_node(st, nodemap, "Height")
    if w_node is None or h_node is None:
        logger.warning("Width/Height nodes missing — leaving ROI unchanged")
        return None
    try:
        w_node.value = int(w_node.max)
        h_node.value = int(h_node.max)
        return int(w_node.value), int(h_node.value)
    except Exception:
        logger.exception("Failed to set Width/Height to max")
        return None


def node_to_ip(node: Any) -> Optional[str]:
    if node is None:
        return None
    try:
        value = node.get()
        if hasattr(value, "to_string"):
            return str(value.to_string())
        return str(value)
    except Exception:
        return None


def node_to_int(node: Any) -> Optional[int]:
    if node is None:
        return None
    try:
        value = node.get()
        if hasattr(value, "value"):
            return int(value.value)
        if hasattr(value, "to_string"):
            text = str(value.to_string()).strip()
            if "." in text:
                import ipaddress

                return int(ipaddress.ip_address(text))
            return int(text, 0)
        return int(value)
    except Exception:
        return None
