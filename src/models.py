#!/usr/bin/env python
from __future__ import annotations
from typing import Optional, List, Dict
from dataclasses import dataclass, asdict
import redis
import dataclasses
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class COLORS:
    """
    Enumeration of codes to manipulate the colors written to terminal.
    """

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class Screen(Enum):
    """
    Enumeration of the different views or screens in the
    monitor switch command.
    """

    MAIN = "main"
    INTERFACES = "interfaces"
    LLDP = "lldp"


class Common:
    """
    Several commonly used strings and outputs put to use in
     the monitor switch command.
    """

    separator = "-------------"


@dataclass
class PortChannelInterfaceState:
    """
    Describes the PortChannel name and state.
    """

    status: str
    port_channel_name: str


@dataclass
class PortChannelInterfacesState:
    """
    Describes the PortChannels configured on the device along with their
     name as well as their state.
    """

    interfaces: Dict[str, PortChannelInterfaceState]


@dataclass
class Port:
    """
    The interface information as it exists in the PORT_TABLE.
    """

    admin_status: str
    alias: str
    autoneg: str
    index: str
    lanes: str
    mtu: str
    speed: str
    oper_status: str
    preemphasis: Optional[str] = ""
    description: Optional[str] = ""


@dataclass
class RegionTable:
    """
    The MSTP Region information as it exists under the _MSTP_REGION_TABLE:REGION key.
    """

    regionname: str
    revision: str
    bridge_id: str
    bridge_prio: str
    cist_root_bridge_prio: str
    regional_root_bridge_prio: str
    max_age: str
    hello_time: str
    forward_delay: str
    max_hops: str
    last_topology_change: str
    topology_change_count: str
    instances_configured: str
    configuration_digest: str
    cist_root_bridge_id: str
    regional_root_bridge_id: str
    root_max_age: str
    root_hello_time: str
    root_forward_delay: str
    root_port: str
    root_max_hops: str
    internal_path_cost: Optional[str] = None
    external_path_cost: Optional[str] = None


@dataclass
class LLDPEntry:
    """
    LLDP neighbor information as it exists under the 'LLDP_ENTRY_TABLE:xxx' keys.
    """

    lldp_rem_man_addr: str
    lldp_rem_sys_cap_enabled: str
    lldp_rem_index: str
    lldp_rem_sys_desc: str
    lldp_rem_sys_cap_supported: str
    lldp_rem_port_id: str
    lldp_rem_sys_name: str
    lldp_rem_chassis_id: str
    lldp_rem_port_desc: str
    lldp_rem_time_mark: str
    lldp_rem_chassis_id_subtype: str
    lldp_rem_port_id_subtype: str


@dataclass
class LLDPLocalChassis:
    """
    The LLDP information that is send to other devices.
    """

    lldp_loc_sys_cap_supported: str
    lldp_loc_sys_desc: str
    lldp_loc_chassis_id: str
    lldp_loc_sys_cap_enabled: str
    lldp_loc_sys_name: str
    lldp_loc_chassis_id_subtype: str
    lldp_loc_man_addr: str
    ttl: float = -0.001
    expireat: float = 0.0


class SonicDataRetriever:
    """
    Retrieves data from the Redis case and returns
    a named type.
    sdr = SonicDataRetriever()
    sdr.get_lldp_local_chassis()
    sdr.get_all_redis_keys()
    sdr.get_region_table()
    sdr.get_port_value("Ethernet27")
    """

    @staticmethod
    def get_redis_client(host="localhost", port=6379, db=0):
        redis_client = redis.Redis(host=host, port=port, db=db)
        return redis_client

    def hmset(self, key: str, mapping: Dict[str, str]) -> Dict:
        """
        Store target hash in redis
        """
        redis_client = self.get_redis_client()
        return redis_client.hmset(key, mapping)

    def hgetall(self, key: str) -> Dict:
        """
        Returns all fields and values of the hash stored at key.

        In the returned value, every field name is followed by its value,
        so the length of the reply is twice the size of the hash.
        """
        redis_client = self.get_redis_client()
        return redis_client.hgetall(key)

    def hgetall_to_str(self, key: str) -> Dict[str, str]:
        data = self.hgetall(key)
        data_converted = {k.decode("utf-8"): v.decode("utf-8") for k, v in data.items()}
        return data_converted

    def get_port_channel_interfaces_status(self):
        keys = self.get_all_redis_keys()
        port_channel_interfaces_state = PortChannelInterfacesState(interfaces={})

        if keys is None:
            raise RuntimeError("get_all_redis_keys returned None")
        for key in keys:
            # example key that is interesting:
            # 'LAG_MEMBER_TABLE:PortChannel6:Ethernet49'
            if "LAG_MEMBER_TABLE:PortChannel" in key and "Ethernet" in key:
                interface = key.split(":")[-1]
                port_channel = key.split(":")[1]
                port_channel_int_status = sdr.hgetall_to_str(
                    key
                )  # {'status': 'enabled'}
                port_channel_interfaces_state.interfaces[
                    interface
                ] = PortChannelInterfaceState(
                    status=port_channel_int_status["status"],
                    port_channel_name=port_channel,
                )
        return port_channel_interfaces_state

    def get_all_redis_keys(self, db=0) -> Optional[List[str]]:
        """
        Collect all keys from Redis.
        """
        try:
            redis_client = self.get_redis_client(db=db)

            # Use the KEYS command to get all keys
            # Note: Be cautious with this on large databases as it can be slow
            all_keys = redis_client.keys("*")

            # Convert byte strings to regular strings
            all_keys_as_str: List[str] = [key.decode("utf-8") for key in all_keys]

            return all_keys_as_str

        except redis.ConnectionError:
            print("Could not connect to Redis. Please check your connection settings.")

        except Exception as e:
            print(f"An error occurred: {str(e)}")

    def get_port_value(self, interface: str) -> Port:
        redis_client = self.get_redis_client()
        data = redis_client.hgetall(f"PORT_TABLE:{interface}")
        data_converted = {k.decode("utf-8"): v.decode("utf-8") for k, v in data.items()}
        port_table = Port(**data_converted)

        return port_table

    def get_lldp_local_chassis(self) -> Optional[LLDPLocalChassis]:
        """
        Retrieve LLDP local chassis information from Redis..
        """
        try:
            redis_client = self.get_redis_client()
            data = redis_client.hgetall("LLDP_LOC_CHASSIS")
            if isinstance(data, dict):
                decoded_data = {
                    k.decode("utf-8"): v.decode("utf-8") for k, v in data.items()
                }
                return LLDPLocalChassis(**decoded_data)
            else:
                print(f"No LLDP local chassis information found")
                return None
        except Exception as e:
            print(f"Error retrieving LLDP local chassis information: {e}")
            return None

    def get_region_table(self) -> Optional[RegionTable]:
        key = "_MSTP_REGION_TABLE:REGION"
        redis_client = self.get_redis_client()
        data = redis_client.hgetall(key)
        data_converted = {k.decode("utf-8"): v.decode("utf-8") for k, v in data.items()}

        if data_converted:
            return RegionTable(**data_converted)
        else:
            return None

    def get_lldp_entry(self, interface: str) -> Optional[LLDPEntry]:
        """
        Retrieve LLDP entry from Redis.
        """
        redis_client = self.get_redis_client()
        key = f"LLDP_ENTRY_TABLE:{interface}"
        try:
            data = redis_client.hgetall(key)
            if data:
                decoded_data = {
                    k.decode("utf-8"): v.decode("utf-8") for k, v in data.items()
                }
                return LLDPEntry(**decoded_data)
            else:
                print(f"No LLDP entry found for {interface}")
                return None
        except Exception as e:
            print(f"Error retrieving LLDP entry for {interface}: {e}")
            return None

    def store_lldp_entry(self, lldp_entry: LLDPEntry, interface: str):
        """
        Store LLDP entry as a hash in Redis.
        """
        redis_client = self.get_redis_client()
        key = f"LLDP_ENTRY_TABLE:{interface}"
        try:
            redis_client.hmset(key, dataclasses.asdict(lldp_entry))
            print(f"Successfully stored LLDP entry for {interface}")
            return True
        except Exception as e:
            print(f"Error storing LLDP entry for {interface}: {e}")
            return False

    def delete_key(self, key: str) -> None:
        """
        Deletes given key from Redis.

        Example:
        >>> sdr.delete_key("Ethernet28")
        >>> sdr.delete_key("Ethernet27")
        """
        redis_client = self.get_redis_client()
        redis_client.delete(key)


def retrieve_port_table(key: str) -> Port:
    """
    Retrieve a PortTable instance from Redis.

    Args:
        key (str): The key used to store the data in Redis.

    Returns:
        PortTable: The retrieved PortTable instance.
    """
    # Get the data from Redis using the provided key
    data = r.hgetall(key)

    # Convert the data to a dictionary
    data_converted = {k.decode("utf-8"): v.decode("utf-8") for k, v in data.items()}
    # print(data_converted)
    # Convert the 'value' field from JSON string to dictionary
    data_converted_value = {
        k.decode("utf-8"): v.decode("utf-8") for k, v in data_converted["value"].items()
    }
    # Create a PortTable instance from the dictionary
    port_table = Port(**data_converted)

    return port_table




if __name__ == "__main__":
    print(f"{COLORS.WARNING}Warning: change of color. Continue?{COLORS.ENDC}")
    print("normal again")
    sdr = SonicDataRetriever()
    sdr.get_lldp_local_chassis()
    sdr.get_all_redis_keys()
    sdr.get_region_table()
    sdr.get_port_value("Ethernet28")
    sdr.get_lldp_entry("Ethernet48")
    sdr.get_lldp_entry("Ethernet49")
    print(sdr.get_all_redis_keys())
    sdr.get_port_channel_interfaces_status()
