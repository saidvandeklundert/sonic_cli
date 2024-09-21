"""
SONiC Data
"""
import redis
import dataclasses
import logging
from typing import Optional, Dict, List
from dataclasses import dataclass
from enum import Enum

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.WARN)
ch = logging.StreamHandler()
ch.setLevel(logging.WARN)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
LOGGER.addHandler(ch)


class SonicDataException(Exception):
    pass


class SonicConfigKey(Enum):
    DEVICE_METADATA = b"DEVICE_METADATA|localhost"


class SonicDatabase(Enum):
    """
    Enumeration of the different databases available
    on a device running SONiC.

    For more information:
    https://github.com/sonic-net/SONiC/blob/master/doc/system-telemetry/grpc_telemetry.md
    """

    APLL_DB = 0
    ASIC_DB = 1
    COUNTERS_DB = 2
    LOGLEVEL_DB = 3
    CONFIG_DB = 4
    FLEX_COUNTER_DB = 5
    STATE_DB = 6


@dataclass
class SoftwareVersionInformation:
    software_version: str
    hwsku: str
    distribution: str
    kernel: str


@dataclass
class ChassisInfo:
    serial: str
    model: str
    revision: str
    psu_num: str


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
class Ports:
    """
    All the ports on the device
    """

    ports: List[Port]


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
class LLDPEntries:
    """
    LLDP neighbor information as it exists under the 'LLDP_ENTRY_TABLE:xxx' keys.
    """

    lldp_entries: List[LLDPEntry]


@dataclass
class LLDPLocalChassis:
    """
    The LLDP information that is send to other devices.
    """

    lldp_loc_chassis_id: str
    lldp_loc_sys_name: str
    lldp_loc_chassis_id_subtype: str
    lldp_loc_sys_desc: Optional[str] = None
    lldp_loc_man_addr: Optional[str] = None
    lldp_loc_sys_cap_enabled: Optional[str] = None
    lldp_loc_sys_cap_supported: Optional[str] = None


@dataclass
class DeviceMetaData:
    """
    Device metadata as it is configured on the device
    under DEVICE_METADATA.
    """

    buffer_model: str
    default_bgp_status: str
    default_pfcwd_status: str
    hostname: str
    hwsku: str
    platform: str
    mac: str
    synchronous_mode: str
    type: str


class SonicData:
    """
    Work with data on a device running SONiC OS.


    sd = SonicData()
    sd.get_lldp_local_chassis()
    sd.get_all_redis_keys()
    sd.get_region_table()
    sd.get_port_value("Ethernet27")
    """

    @staticmethod
    def get_redis_client(
        host: str = "localhost",
        port: int = 6379,
        db: SonicDatabase = SonicDatabase.APLL_DB,
    ):
        """
        Helper method that instantiates a Redis connection.

        Pooling and re-use is handled by Redis.

        Same as running the following:
        >>> redis_client = redis.Redis(host="localhost", port=6379, db=0)
        """
        redis_client = redis.Redis(host=host, port=port, db=db.value)
        return redis_client

    def delete_key(self, key: str) -> None:
        """
        Deletes given key from Redis.

        Example:
        >>> sdr.delete_key("Ethernet28")
        >>> sdr.delete_key("Ethernet27")
        """
        redis_client = self.get_redis_client()
        redis_client.delete(key)

    def hmset(
        self,
        key: str,
        mapping: Dict[str, str],
        db: SonicDatabase = SonicDatabase.APLL_DB,
    ) -> Dict:
        """
        Store target hash in redis
        """
        redis_client = self.get_redis_client(db=db)
        return redis_client.hmset(key, mapping)

    def hgetall(self, key: str, db: SonicDatabase = SonicDatabase.APLL_DB) -> Dict:
        """
        Returns all fields and values of the hash stored at key.

        If the key does not exist in Redis, an empty dictionary is returned.

        In the returned value, every field name is followed by its value,
        so the length of the reply is twice the size of the hash.
        """
        redis_client = self.get_redis_client(db=db)
        return redis_client.hgetall(key)

    def hgetall_to_str(
        self, key: str, db: SonicDatabase = SonicDatabase.APLL_DB
    ) -> Dict[str, str]:
        """
        Decodes the values stored in Redis and returns every mapping as holding strings.

        If the 'hgetall' method retrieves a key that does not existin Redis, this method
        returns an empty dictionary.


        """
        data = self.hgetall(key=key, db=db)
        data_converted = {k.decode("utf-8"): v.decode("utf-8") for k, v in data.items()}
        return data_converted

    def search_keys(
        self, substring, db: SonicDatabase = SonicDatabase.APLL_DB
    ) -> List[str]:
        """
        Search Redis for all keys containing a given substring.
        """
        try:
            redis_client = self.get_redis_client(db=db)

            matching_keys = []
            cursor = 0
            while True:
                cursor, keys = redis_client.scan(
                    cursor=cursor, match=f"*{substring}*", count=100
                )
                matching_keys.extend([key.decode("utf-8") for key in keys])
                if cursor == 0:
                    break

            return matching_keys

        except redis.RedisError as e:
            print(f"Redis error occurred: {e}")
            return []

        except Exception as e:
            print(f"An error occurred: {e}")
            return []

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
                port_channel_int_status = self.hgetall_to_str(
                    key
                )  # {'status': 'enabled'}
                port_channel_interfaces_state.interfaces[
                    interface
                ] = PortChannelInterfaceState(
                    status=port_channel_int_status["status"],
                    port_channel_name=port_channel,
                )
        return port_channel_interfaces_state

    def get_all_redis_keys(
        self, db: SonicDatabase = SonicDatabase.APLL_DB
    ) -> Optional[List[str]]:
        """
        Collect all keys from Redis.
        """
        redis_client = self.get_redis_client(db=db)
        all_keys = redis_client.keys("*")
        all_keys_as_str: List[str] = [key.decode("utf-8") for key in all_keys]
        return all_keys_as_str

    def get_port_value(
        self, interface: Optional[str] = None, key: Optional[str] = None
    ) -> Port:
        """
        Get the Port model for a single interface.
        """
        return self.get_port(interface=interface, key=key)

    def get_port(
        self, interface: Optional[str] = None, key: Optional[str] = None
    ) -> Port:
        """
        Get the Port model for a single interface.
        """
        if isinstance(interface, str) is False and isinstance(key, str) is False:
            raise SonicDataException(
                f"either interface or key needs to be a string value."
            )
        elif isinstance(interface, str) is True and isinstance(key, str) is True:
            raise SonicDataException(
                f"interface and key cannot both be set a string value, choose one or the other"
            )
        if interface:
            data = self.hgetall_to_str(f"PORT_TABLE:{interface}")
        else:
            data = self.hgetall_to_str(key=key)
        LOGGER.debug(data)
        port_table = Port(**data)

        return port_table

    def get_all_ports(self) -> Ports:
        """
        Collect and return every Port inside a 'Ports'.
        """
        all_ports = Ports(ports=[])
        interesting_keys = self.search_keys("PORT_TABLE:Eth")
        interesting_keys = [
            key for key in interesting_keys if key.startswith("PORT_TABLE:")
        ]
        for key in interesting_keys:
            port = self.get_port(key=key)
            if port:
                all_ports.ports.append(port)
        return all_ports

    def get_lldp_local_chassis(self) -> Optional[LLDPLocalChassis]:
        """
        Retrieve LLDP local chassis information from Redis..
        """
        data = self.hgetall_to_str("LLDP_LOC_CHASSIS")
        return LLDPLocalChassis(**data)

    def get_software_version_information(self) -> SoftwareVersionInformation:
        """
        class SoftwareVersionInformation:
            software_version: str
            hwsku: str
            distribution:str
            kernel:str

        """
        software_version_information = {
            "software_version": "",
            "hwsku": "",
            "distribution": "",
            "kernel": "",
        }
        lldp_local_chassis_information = self.get_lldp_local_chassis()
        if lldp_local_chassis_information is None:
            raise SonicDataException("LLDPLocalChassis should contain a non-None value")
        elif not isinstance(lldp_local_chassis_information.lldp_loc_sys_desc, str):
            raise SonicDataException(
                "LLDPLocalChassis should contain attribute lldp_loc_sys_desc for this method"
            )

        sys_desc_values = lldp_local_chassis_information.lldp_loc_sys_desc.split(" - ")
        for val in sys_desc_values:
            if val.startswith("SONiC Software Version"):
                value = val.split(":")[-1].strip()
                software_version_information["software_version"] = value
            if val.startswith("HwSku:"):
                value = val.split(":")[-1].strip()
                software_version_information["hwsku"] = value
            if val.startswith("Distribution:"):
                value = val.split(":")[-1].strip()
                software_version_information["distribution"] = value
            if val.startswith("Kernel:"):
                value = val.split(":")[-1].strip()
                software_version_information["kernel"] = value

        return SoftwareVersionInformation(**software_version_information)

    def get_region_table(self) -> Optional[RegionTable]:
        """
        Retrieve MSTP information from SONiC.
        """
        data = self.hgetall_to_str("_MSTP_REGION_TABLE:REGION")
        return RegionTable(**data)

    def get_lldp_entry(
        self, interface: Optional[str] = None, key: Optional[str] = None
    ) -> Optional[LLDPEntry]:
        """
        Retrieve LLDP entry from Redis.

        Either submit the interface name or the entry from DB0.
        """
        if isinstance(interface, str) is False and isinstance(key, str) is False:
            raise SonicDataException(
                f"either interface or key needs to be a string value."
            )
        elif isinstance(interface, str) is True and isinstance(key, str) is True:
            raise SonicDataException(
                f"interface and key cannot both be set a string value, choose one or the other"
            )
        if interface:
            data = self.hgetall_to_str(f"LLDP_ENTRY_TABLE:{interface}")
        else:
            data = self.hgetall_to_str(key=key)

        return LLDPEntry(**data)

    def get_all_lldp_entries(self) -> LLDPEntries:
        """
        Collect and return every LLDPEntry inside an LLDPEntries.
        """
        lldp_entries = LLDPEntries(lldp_entries=[])
        lldp_entry_keys = self.search_keys("LLDP_ENTRY")
        for key in lldp_entry_keys:
            lldp_entry = self.get_lldp_entry(key=key)
            if lldp_entry:
                lldp_entries.lldp_entries.append(lldp_entry)
        return lldp_entries

    def get_chassis_information(self) -> List[ChassisInfo]:
        """
        Collect and return ChassisInfo for all chassis
        """
        self.search_keys(substring="PROCESS", db=SonicDatabase.STATE_DB)
        chassis_info = []
        chassis = self.search_keys(
            substring="CHASSIS_INFO|chassis", db=SonicDatabase.STATE_DB
        )
        for key in chassis:
            data = self.hgetall_to_str(key=key, db=SonicDatabase.STATE_DB)
            if data:
                chassis_info.append(ChassisInfo(**data))

        return chassis_info

    def store_lldp_entry(self, lldp_entry: LLDPEntry, interface: str):
        """
        Store LLDP entry as a hash in Redis.
        """
        redis_client = self.get_redis_client()
        key = f"LLDP_ENTRY_TABLE:{interface}"
        try:
            redis_client.hmset(key, dataclasses.asdict(lldp_entry))
            LOGGER.debug(f"Successfully stored LLDP entry for {interface}")
            return True
        except Exception as e:
            LOGGER.error(f"Error storing LLDP entry for {interface}: {e}")
            return False

    def get_config_device_metadata(self) -> DeviceMetaData:
        data = self.hgetall_to_str(
            b"DEVICE_METADATA|localhost", SonicDatabase.CONFIG_DB
        )
        LOGGER.debug(data)
        return DeviceMetaData(**data)
