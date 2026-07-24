"""Omron GigE IP pool assignment (ForceIP + ping probe)."""

from __future__ import annotations

import ipaddress
import shutil
import subprocess
from typing import Any, List, Optional, Set

from loguru import logger

from src.camera.omron_nodes import node_to_int, node_to_ip
from src.utils.color import green, red


def pool_ips(cidr: str) -> List[str]:
    try:
        return [str(ip) for ip in ipaddress.ip_network(cidr, strict=False).hosts()]
    except Exception:
        logger.exception("Invalid camera IP pool CIDR: {}", cidr)
        return []


def is_ip_reachable(ip: str, timeout_seconds: float = 0.4) -> bool:
    ping_binary = shutil.which("ping")
    if ping_binary is None:
        return False
    try:
        result = subprocess.run(
            [ping_binary, "-c", "1", "-W", str(max(1, int(timeout_seconds))), ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=max(1.0, timeout_seconds + 0.2),
            check=False,
        )
    except Exception:
        return False
    return result.returncode == 0


def _compatible(ip_str: str, iface_ip_int: int, iface_mask_int: int) -> bool:
    try:
        ip_int = int(ipaddress.ip_address(ip_str))
    except Exception:
        return False
    if ip_int in (0, iface_ip_int) or ip_str in {"0.0.0.0", "255.255.255.255"}:
        return False
    return (iface_ip_int & iface_mask_int) == (ip_int & iface_mask_int)


def _pick_ip(
    preferred: List[str],
    fallback: List[str],
    assigned: Set[str],
    iface_ip_int: int,
    iface_mask_int: int,
) -> Optional[str]:
    for ip in preferred + fallback:
        if ip in assigned:
            continue
        if _compatible(ip, iface_ip_int, iface_mask_int):
            return ip
    return None


def _read_device_ip(nodemap: Any) -> Optional[str]:
    for key in ("GevCurrentIPAddress", "GevDeviceIPAddress", "GevDeviceCurrentIPAddress"):
        node = nodemap.get_node(key)
        as_int = node_to_int(node)
        if as_int:
            try:
                ip_str = str(ipaddress.ip_address(as_int))
                if ip_str not in {"0.0.0.0", "255.255.255.255"}:
                    return ip_str
            except Exception:
                pass
        as_str = node_to_ip(node)
        if as_str and as_str not in {"0.0.0.0", "255.255.255.255"}:
            return as_str
    return None


def _read_serial(nodemap: Any) -> str:
    for key in ("GevDeviceSerialNumber", "DeviceSerialNumber"):
        try:
            node = nodemap.get_node(key)
            if node is None:
                continue
            value = node.get()
            serial = str(value.to_string() if hasattr(value, "to_string") else value)
            if serial:
                return serial
        except Exception:
            continue
    return "unknown"


def auto_assign_ips(st: Any, system: Any, *, ip_pool_cidr: str, preferred: List[str]) -> None:
    """ForceIP cameras on each interface into the CIDR pool when needed."""
    if not ip_pool_cidr:
        raise ValueError("ip_pool_cidr must be configured for Omron IP assignment")
    assigned: Set[str] = set()
    preferred = list(preferred)
    fallback = pool_ips(ip_pool_cidr)
    assigned_n = already_n = 0
    logger.info("Omron IP assignment from {}", ip_pool_cidr)

    for index in range(system.interface_count):
        iface = system.get_interface(index)
        nodemap = iface.port.nodemap
        iface_ip = node_to_ip(nodemap.get_node("GevInterfaceSubnetIPAddress"))
        iface_mask = node_to_int(nodemap.get_node("GevInterfaceSubnetMask"))
        if not iface_ip or iface_mask is None:
            logger.warning("Skipping interface {}: subnet unreadable", index)
            continue
        iface_ip_int = int(ipaddress.ip_address(iface_ip))
        assigned.add(iface_ip)

        for device_idx in range(iface.device_count):
            selector = nodemap.get_node("DeviceSelector")
            if selector is None:
                continue
            st.PyIInteger(selector).value = device_idx
            force_ip = nodemap.get_node("GevDeviceForceIPAddress")
            force_mask = nodemap.get_node("GevDeviceForceSubnetMask")
            force_cmd = nodemap.get_node("GevDeviceForceIP")
            if force_ip is None or force_mask is None or force_cmd is None:
                continue
            serial = _read_serial(nodemap)
            current_ip = _read_device_ip(nodemap)
            if (
                current_ip
                and _compatible(current_ip, iface_ip_int, iface_mask)
                and is_ip_reachable(current_ip)
            ):
                assigned.add(current_ip)
                already_n += 1
                logger.info(green(f"Omron {serial} already at {current_ip}"))
                continue
            while True:
                desired = _pick_ip(preferred, fallback, assigned, iface_ip_int, iface_mask)
                if desired is None:
                    logger.warning(red(f"No IP for iface {index} device {device_idx}"))
                    break
                if is_ip_reachable(desired):
                    assigned.add(desired)
                    if current_ip == desired:
                        already_n += 1
                        break
                    logger.warning(red(f"Skip {desired}: responds to ping"))
                    continue
                try:
                    force_ip.value = int(ipaddress.ip_address(desired))
                    force_mask.value = iface_mask
                    st.PyICommand(force_cmd).execute()
                    assigned.add(desired)
                    assigned_n += 1
                    logger.info(green(f"Assigned Omron {serial} -> {desired}"))
                    break
                except Exception as exc:
                    assigned.add(desired)
                    logger.warning(red(f"ForceIP {desired} failed: {exc}"))

    if assigned_n == 0 and already_n == 0:
        logger.warning("IP assignment found 0 devices (cidr={})", ip_pool_cidr)
    else:
        logger.info("IP assignment: {} forced, {} already ok", assigned_n, already_n)
