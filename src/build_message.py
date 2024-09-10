#!/usr/bin/env python
from models import SonicDataRetriever, COLORS, Screen, Common, LLDPEntry
import datetime
from typing import List


COMMON = Common()


def build_message(message: Screen) -> str:
    """
    Build the message that will be presented to the terminal
    """
    screen_display = []
    screen_display.extend(build_message_header(message))
    sdr = SonicDataRetriever()
    redis_keys = sdr.get_all_redis_keys()
    if not isinstance(redis_keys, list):
        raise RuntimeError("get_all_redis_keys should have returned a list")
    if message == Screen.MAIN:
        sdr = SonicDataRetriever()
        local_chassis = sdr.get_lldp_local_chassis()
        if local_chassis:
            screen_display.append(f"local_chassis: {local_chassis.lldp_loc_sys_name}")
        screen_display.extend(build_mstp_info())
        screen_display.append(COMMON.separator)
        interfaces_message = build_message_interfaces(redis_keys=redis_keys)
        screen_display.extend(interfaces_message)
    elif message == Screen.INTERFACES:
        screen_display.append(COMMON.separator)
        screen_display.extend(build_message_interfaces(redis_keys=redis_keys))
    elif message == Screen.LLDP:
        screen_display.append(COMMON.separator)
        screen_display.extend(build_message_lldp_neighbors(redis_keys=redis_keys))
    screen_display.append(COMMON.separator)
    return "\n".join(screen_display)


def display_neighbor(lldp_entry: LLDPEntry, local_interface: str) -> List[str]:
    message = f"""
Local interface: {local_interface}
  - remote device: {lldp_entry.lldp_rem_sys_name}
  - remote interface: {lldp_entry.lldp_rem_port_id}
  - remote system descruption: {lldp_entry.lldp_rem_sys_desc}
"""
    return message.splitlines()


def build_message_lldp_neighbors(redis_keys: List[str]) -> List[str]:
    message = []
    sdr = SonicDataRetriever()
    for key in redis_keys:
        if key.startswith("LLDP_ENTRY_TABLE"):
            interface = key.split(":")[-1]
            lldp_entry = sdr.get_lldp_entry(interface=interface)
            if lldp_entry:
                message.extend(display_neighbor(lldp_entry, interface))

    return message


def build_message_header(screen: Screen) -> List[str]:
    message = []
    views = f"""
Current view {screen.value}

The following views exist:
i or interface for interface information
l or lldp for lldp information
m or main for the main screen

hit 'q' to quit"""
    message.append("-----------------")
    message.append("\n")
    message.append(f"Current time: {str(datetime.datetime.now())}")
    message.append(views)
    return message


def build_mstp_info() -> List[str]:
    screen_display = []
    sdr = SonicDataRetriever()
    region_table = sdr.get_region_table()
    if region_table:
        screen_display.append(
            f"local cid {region_table.bridge_id}, root {region_table.cist_root_bridge_id}"
        )
        screen_display.append(f"root port: {region_table.root_port}")
        screen_display.append(
            f"time since last topology change (sec): {region_table.last_topology_change}"
        )
    return screen_display


def build_message_interfaces(redis_keys: List[str]) -> List[str]:
    sdr = SonicDataRetriever()
    screen_display = []
    for key in redis_keys:
        if key.startswith("PORT_TABLE:Ethernet"):
            interface_name = key.split(":")[1]
            try:
                res = sdr.get_port_value(interface=interface_name)

                if res.oper_status == "up":
                    interface_status = f"{COLORS.OKGREEN}{interface_name} is {res.oper_status} {COLORS.ENDC}"
                else:
                    interface_status = f"{COLORS.FAIL}{interface_name} is {res.oper_status} {COLORS.ENDC}"
                screen_display.append(interface_status)
            except Exception:
                pass
    return screen_display
