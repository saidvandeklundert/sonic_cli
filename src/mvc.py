#!/usr/bin/env python
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Union, Tuple
from abc import ABC, abstractmethod
from enum import Enum
import time
import datetime
import sys
import os
import signal
import threading
import queue
import shutil

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


"""
Colors
"""


class ScreenList(list):
    def _append_color(self, color_code: Union[int, str], text: str):
        return f"\033[{color_code}m{text}\033[0m"

    def append_red(self, text: str):
        return self.append(self._append_color(31, text))

    def append_green(self, text: str):
        return self.append(self._append_color(32, text))

    def append_yellow(self, text: str):
        return self.append(self._append_color(33, text))

    def append_blue(self, text: str):
        return self.append(self._append_color(34, text))

    def append_magenta(self, text: str):
        return self.append(self._append_color(35, text))

    def append_cyan(self, text: str):
        return self.append(self._append_color(36, text))

    def append_white(self, text: str):
        return self.append(self._append_color(37, text))

    def append_black(self, text: str):
        return self.append(self._append_color(30, text))

    def append_bold(self, text: str):
        return self.append(self._append_color(1, text))

    def append_underline(self, text: str):
        return self.append(self._append_color(4, text))

    def append_gold(self, text: str):
        return self.append(self._append_color("38;5;220", text))

    def append_light_yellow(self, text: str):
        return self.append(self._append_color("38;5;228", text))

    def append_khaki(self, text: str):
        return self.append(self._append_color("38;5;185", text))

    def append_goldenrod(self, text: str):
        return self.append(self._append_color("38;5;178", text))


@dataclass
class UserScreen:
    screen_lines: ScreenList


"""
Input thread
"""
message_queue: queue.Queue[Union[Screen, float]] = queue.Queue()


def clear_screen():
    """Clears the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def display_message(message):
    """Displays the given message on the screen."""
    clear_screen()
    print(message)


def signal_handler(signal, frame):
    """Handles the signal for graceful exit."""
    print("\nExiting...")
    sys.exit(0)


# Register the signal handler for SIGINT (Ctrl+C)
signal.signal(signal.SIGINT, signal_handler)


def input_thread_function():
    """
    Thread that constantly listens for user input.

    Either halts the program or uses a message queue to flip the view.
    """
    while True:
        line = input()
        if line.lower() == "q":
            print("\nExiting...")
            os._exit(0)  # Exit the entire process
        elif line.lower() == "i" or line == "interface":
            message_queue.put(Screen.INTERFACE_VIEW)
            print("change to interface view")
        elif line.lower() == "m" or line == "main":
            message_queue.put(Screen.MAIN_VIEW)
            print("change to main view")
        elif line.lower() == "l" or line == "lldp":
            message_queue.put(Screen.LLDP_VIEW)
            print("change to main view")
        elif len(line) >= 1 and line[0].isdigit():
            new_interval = float(line)
            message_queue.put(new_interval)
            print("change interval")
        else:
            print(f"{line} is not a valid input option.")
        print(f"selection input: {line}")


"""
The Controller portion of the program
"""


class Screen(str, Enum):
    """
    THe different screens available for selection.
    """

    MAIN_VIEW = "main"
    INTERFACE_VIEW = "interface"
    LLDP_VIEW = "lldp"


@dataclass
class Configuration:
    """
    Program configuration with sensible defaults.

    interval: refresh rate of the program.
    screen: determines what view should be presented to the user.
    test: should be set to False in case the program is running
     on the device, set it to True otehrwise.
    """

    interval: float = 1.0
    screen: Screen = Screen.MAIN_VIEW
    test: bool = True


class Controller:
    """
    Controller class of the program.

    Periodically selects and fetches the required data, which is then
    passed on to proper view class. The result is displayed to screen.
    """

    def __init__(self, configuration: Configuration = Configuration()):
        self.configuration = configuration

    def display_screen(self, screen: Screen) -> None:
        """
        Based on the screen, collect the proper model and use that to build the
         view that is selected.
        """
        data = data_model_builder(screen, self.configuration.test)
        view = view_builder(screen=screen, data=data)

        def print_at_top(content):
            # clear screen:
            sys.stdout.write("\033[2J")
            # cursor to (0, 0)
            sys.stdout.write("\033[H")
            print(content)
            sys.stdout.flush()

        print_at_top(view.render())

    @staticmethod
    def flip_screen_or_set_interval(
        screen: Screen, interval: float
    ) -> Tuple[Screen, float]:
        """
        Communicate to the input thread and:
        - instruct the view to change
        - change the interval at which the program runs
        """
        if not message_queue.empty():
            message_from_queue = message_queue.get(1)
            if isinstance(message_from_queue, Screen):
                print(message_from_queue)
                # raise RuntimeError("ee")
                screen = message_from_queue
                return (message_from_queue, interval)
            elif isinstance(message_from_queue, float):
                interval = message_from_queue
                return (screen, message_from_queue)

        return (screen, interval)

    def run(self) -> None:
        """
        Run the application.

        Starts an input thread that listens for user input and runs the rest of the
         program under the main thread.
        """
        # start the input thread:
        input_thread = threading.Thread(target=input_thread_function)
        input_thread.daemon = (
            True  # Allow the thread to exit when the main program exits
        )
        input_thread.start()
        interval = self.configuration.interval
        screen_value = self.configuration.screen
        try:
            while True:
                screen_value, interval = self.flip_screen_or_set_interval(
                    screen_value, interval
                )
                time.sleep(interval)
                self.display_screen(screen=screen_value)

                columns, lines = shutil.get_terminal_size()
                # Print the terminal size
                print(f"Terminal size: {columns} columns, {lines} lines")
        except KeyboardInterrupt:
            # Handle the KeyboardInterrupt exception (Ctrl+C)
            print("\nExiting monitor tool...")


"""
The model portion of the program
"""


@dataclass
class ViewData:
    ...


@dataclass
class MainViewData(ViewData):
    """
    Data required to render the 'MainView'.
    """

    hostname: str
    software_version: str
    linux_distro: str
    kernel_version: str
    model: str
    lldp_neighbors: List[str]
    screen: Screen = Screen.MAIN_VIEW


@dataclass
class InterfaceViewData(ViewData):
    hostname: str
    software_version: str
    model: str
    ports: Ports
    port_channels: PortChannelInterfacesState
    screen: Screen = Screen.INTERFACE_VIEW


@dataclass
class LldpViewData(ViewData):
    hostname: str
    software_version: str
    model: str
    neighbors: LLDPEntries
    screen: Screen = Screen.LLDP_VIEW


ScreenData = Union[MainViewData, InterfaceViewData, LldpViewData]


def data_model_builder(
    screen: Screen = Screen.MAIN_VIEW, test: bool = True
) -> ScreenData:
    """
    Returnes a data model to seed one of the 'Screen' types that are supported.
    """
    builder_data = {
        "main": main_view_model_builder,
        "interface": interface_view_model_builder,
        "lldp": lldp_view_model_builder,
    }
    return builder_data[screen.value](test)


def main_view_model_builder(test: bool) -> MainViewData:
    """
    Builds the model that allows for the rendering
     of the main view.

    When test is set to True, the model data is seeded from a constant
    """
    if test is True:
        return MainViewData(
            hostname=device_meta_data.hostname,
            software_version=software_information.software_version,
            linux_distro=software_information.distribution,
            kernel_version=software_information.kernel,
            model=device_meta_data.hwsku,
            lldp_neighbors=lldp_neighbor_names,
        )
    else:
        sd = SonicData()
        retrieved_meta_data = sd.get_config_device_metadata()
        retrieved_software_information = sd.get_software_version_information()
        retrieved_lldp_entries = sd.get_all_lldp_entries()
        retrieved_lldp_neighbor_names = [
            lldp_entry.lldp_rem_sys_name
            for lldp_entry in retrieved_lldp_entries.lldp_entries
        ]
        return MainViewData(
            hostname=retrieved_meta_data.hostname,
            software_version=retrieved_software_information.software_version,
            linux_distro=retrieved_software_information.distribution,
            kernel_version=retrieved_software_information.kernel,
            model=retrieved_meta_data.hwsku,
            lldp_neighbors=retrieved_lldp_neighbor_names,
        )


def interface_view_model_builder(test: bool) -> InterfaceViewData:
    """
    Builds the model that allows for the rendering
     of the interface view.
    """
    if test is True:
        return InterfaceViewData(
            hostname=device_meta_data.hostname,
            software_version=software_information.software_version,
            model=device_meta_data.hwsku,
            ports=all_ports,
            port_channels=port_channel_state,
        )
    else:
        sd = SonicData()
        retrieved_meta_data = sd.get_config_device_metadata()
        retrieved_all_ports = sd.get_all_ports()
        retrieved_software_information = sd.get_software_version_information()
        retrieved_port_channels = sd.get_port_channel_interfaces_status()
        return InterfaceViewData(
            hostname=retrieved_meta_data.hostname,
            software_version=retrieved_software_information.software_version,
            model=retrieved_meta_data.hwsku,
            ports=retrieved_all_ports,
            port_channels=retrieved_port_channels,
        )


def lldp_view_model_builder(test: bool) -> LldpViewData:
    """
    Builds the model that allows for the rendering
     of the lldp view.
    """
    if test is True:
        return LldpViewData(
            hostname=device_meta_data.hostname,
            model=device_meta_data.hwsku,
            software_version=software_information.software_version,
            neighbors=lldp_entries,
        )
    else:
        sd = SonicData()
        retrieved_meta_data = sd.get_config_device_metadata()
        retrieved_lldp_entries = sd.get_all_lldp_entries()
        retrieved_software_information = sd.get_software_version_information()

        return LldpViewData(
            hostname=retrieved_meta_data.hostname,
            model=retrieved_meta_data.hwsku,
            software_version=retrieved_software_information.software_version,
            neighbors=retrieved_lldp_entries,
        )


"""
The view portion of the program
"""


@dataclass
class TerminalSize:
    """
    The terminal size. The lines indicate the height of the screen and the columns
     indicate the width.
    """

    columns: int
    lines: int


class View(ABC):
    @abstractmethod
    def render(self) -> str:
        ...

    @staticmethod
    def get_terminal_size() -> TerminalSize:
        """
        Returns information about the current terminal.
        """
        columns, lines = shutil.get_terminal_size()
        return TerminalSize(columns=columns, lines=lines)

    def section_separator(self) -> str:
        """
        Return a defaul section separator.
        """
        terminal_size = self.get_terminal_size()

        return f"{terminal_size.columns * '-'}"

    def sub_section_separator(self) -> str:
        """
        Return a defaul section separator.
        """
        terminal_size = self.get_terminal_size()

        return f"{terminal_size.columns * '.'}"

    def footer_and_return(self, view: ScreenList) -> str:
        """
        Appends the default footer to the screen and builds the string.
        """

        view.append_yellow(self.section_separator())
        view.append_khaki(
            "Screen selection: 'i/interface', 'l/lldp', 'm/main', 'q/quit' or a float to change the interval",
        )

        view.append_yellow(self.section_separator())
        return "\n".join(view)

    def header(self, data: ViewData) -> ScreenList:
        """
        Appends the default footer to the screen and builds the string.
        """
        header = ScreenList()
        header.append_yellow(self.section_separator())

        header.append_goldenrod(
            f"System name: {data.hostname} | Current view: {data.screen.value} | Current time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}"
        )
        header.append_yellow(self.section_separator())
        return header


class MainView(View):
    """
    The 'MainView' or the initial page of the CLI.
    """

    def __init__(self, data: MainViewData):
        super().__init__()
        self.data = data

    def render(self) -> str:
        user_screen = self.header(self.data)
        user_screen.append_light_yellow(f"System model: {self.data.model}")
        user_screen.append_light_yellow(f"System version: {self.data.software_version}")
        user_screen.append_light_yellow(f"Kernel version: {self.data.kernel_version}")
        user_screen.append_light_yellow(f"Detected LLDP neighbors: {len(self.data.lldp_neighbors)}")

        return self.footer_and_return(user_screen)


class InterfacesView(View):
    """
    The 'InterfacesView' with detailed interface information.
    """

    def __init__(self, data: InterfaceViewData):
        super().__init__()
        self.data = data

    def render(self) -> str:
        user_screen = self.header(self.data)
        user_screen.append_light_yellow(self.sub_section_separator())
        user_screen.append_gold(f"Port information:")
        user_screen.append_light_yellow(self.sub_section_separator())
        for interface in self.data.ports.ports:
            if interface.admin_status == "up":
                description = interface.description if interface.description else ""
                line = f"{interface.alias} admin status: {interface.admin_status} oper status: {interface.oper_status} description: {description}"
                if interface.oper_status == "up":
                    user_screen.append_green(line)
                else:
                    user_screen.append_red(line)

        user_screen.append_light_yellow(self.sub_section_separator())
        user_screen.append_gold(f"Port channel information:")
        user_screen.append_light_yellow(self.sub_section_separator())

        for int_name, port_channel_state in self.data.port_channels.interfaces.items():
            user_screen.append_green(
                f"{port_channel_state.port_channel_name} {port_channel_state.status} - interface: {int_name}"
            )
        return self.footer_and_return(user_screen)


class LldpView(View):
    """
    The 'LldpView' with detailed neighbor information.
    """

    def __init__(self, data: LldpViewData):
        super().__init__()
        self.data = data

    def render(self) -> str:
        user_screen = self.header(self.data)
        user_screen.append(f"Known LLDP neighbors:")
        user_screen.append_light_yellow(self.sub_section_separator())
        user_screen.append_gold(
            f"{'Sytem name':<45} | {'local port':<20} | {'remote port':<20}"
        )
        for neighbor in self.data.neighbors.lldp_entries:
            user_screen.append_light_yellow(self.sub_section_separator())
            user_screen.append(
                f"{neighbor.lldp_rem_sys_name:<45} | {neighbor.lldp_rem_port_id:<20} | {neighbor.lldp_rem_port_id:<20}"
            )

        user_screen.append_light_yellow(self.sub_section_separator())
        return self.footer_and_return(user_screen)


def view_builder(data, screen: Screen = Screen.MAIN_VIEW) -> View:
    """
    Returns one of the 'View' classes that can be used to render the view.
    """

    if screen == Screen.MAIN_VIEW:
        return MainView(data=data)
    elif screen == Screen.INTERFACE_VIEW:
        return InterfacesView(data=data)
    elif screen == Screen.LLDP_VIEW:
        return LldpView(data=data)
    else:
        raise RuntimeError("Unknown screen selected")


"""
Seed or testing data
"""
local_chassis = LLDPLocalChassis(
    lldp_loc_sys_cap_supported="28 00",
    lldp_loc_sys_desc="SONiC Software Version: SONiC.SONiC-AX-2210-202211.0-22072024 - HwSku: Accton-AS4630-54PE - Distribution: Debian 11.10 - Kernel: 5.10.0-18-2-amd64",
    lldp_loc_chassis_id="90:2d:77:51:78:70",
    lldp_loc_sys_cap_enabled="28 00",
    lldp_loc_sys_name="ausffnx1-fc-acc-sw-1-6",
    lldp_loc_chassis_id_subtype="4",
    lldp_loc_man_addr="7.32.1.6",
)
port_channel_state = PortChannelInterfacesState(
    interfaces={
        "Ethernet48": PortChannelInterfaceState(
            status="enabled", port_channel_name="PortChannel6"
        ),
        "Ethernet49": PortChannelInterfaceState(
            status="enabled", port_channel_name="PortChannel6"
        ),
    }
)
device_meta_data = DeviceMetaData(
    buffer_model="traditional",
    default_bgp_status="up",
    default_pfcwd_status="disable",
    hostname="CBS01",
    hwsku="Accton-AS4630-54PE",
    platform="x86_64-accton_as4630_54pe-r0",
    mac="b4:6a:d4:23:d5:42",
    synchronous_mode="enable",
    type="ToRRouter",
)
lldp_entries = LLDPEntries(
    lldp_entries=[
        LLDPEntry(
            lldp_rem_man_addr="7.32.1.40,2605:b140:100:1001::d:1",
            lldp_rem_sys_cap_enabled="28 00",
            lldp_rem_index="1",
            lldp_rem_sys_desc="Cisco IOS Software [Amsterdam], Catalyst L3 Switch Software (CAT9K_IOSXE), Version 17.3.3, RELEASE SOFTWARE (fc7)\nTechnical Support: http://www.cisco.com/techsupport\nCopyright (c) 1986-2021 by Cisco Systems, Inc.\nCompiled Thu 04-Mar-21 12:32 by mcpre",
            lldp_rem_sys_cap_supported="28 00",
            lldp_rem_port_id="Te1/0/6",
            lldp_rem_sys_name="DAR-01",
            lldp_rem_chassis_id="7c:ad:4f:b1:15:00",
            lldp_rem_port_desc="",
            lldp_rem_time_mark="94821",
            lldp_rem_chassis_id_subtype="4",
            lldp_rem_port_id_subtype="5",
        ),
        LLDPEntry(
            lldp_rem_man_addr="7.32.1.40,2605:b140:100:1001::d:1",
            lldp_rem_sys_cap_enabled="28 00",
            lldp_rem_index="1",
            lldp_rem_sys_desc="Cisco IOS Software [Amsterdam], Catalyst L3 Switch Software (CAT9K_IOSXE), Version 17.3.3, RELEASE SOFTWARE (fc7)\nTechnical Support: http://www.cisco.com/techsupport\nCopyright (c) 1986-2021 by Cisco Systems, Inc.\nCompiled Thu 04-Mar-21 12:32 by mcpre",
            lldp_rem_sys_cap_supported="28 00",
            lldp_rem_port_id="Te2/0/6",
            lldp_rem_sys_name="DAR-01",
            lldp_rem_chassis_id="7c:ad:4f:b1:15:00",
            lldp_rem_port_desc="",
            lldp_rem_time_mark="94821",
            lldp_rem_chassis_id_subtype="4",
            lldp_rem_port_id_subtype="5",
        ),
    ]
)
software_information = SoftwareVersionInformation(
    software_version="SONiC.SONiC-AX-2210-202211.0-22072024",
    hwsku="Accton-AS4630-54PE",
    distribution="Debian 11.10",
    kernel="5.10.0-18-2-amd64",
)
all_ports = Ports(
    ports=[
        Port(
            admin_status="down",
            alias="Eth35(Port35)",
            autoneg="on",
            index="35",
            lanes="12",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth47(Port47)",
            autoneg="on",
            index="47",
            lanes="24",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth5(Port5)",
            autoneg="on",
            index="5",
            lanes="30",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth16(Port16)",
            autoneg="on",
            index="16",
            lanes="35",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth44(Port44)",
            autoneg="on",
            index="44",
            lanes="19",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="up",
            alias="Eth50(Port50)",
            autoneg="off",
            index="50",
            lanes="66",
            mtu="9100",
            speed="10000",
            oper_status="up",
            preemphasis="0x124106",
            description="DAR-01 Te2/0/6",
        ),
        Port(
            admin_status="down",
            alias="Eth9(Port9)",
            autoneg="on",
            index="9",
            lanes="38",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth34(Port34)",
            autoneg="on",
            index="34",
            lanes="9",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth19(Port19)",
            autoneg="on",
            index="19",
            lanes="48",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth39(Port39)",
            autoneg="on",
            index="39",
            lanes="16",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth23(Port23)",
            autoneg="on",
            index="23",
            lanes="44",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth4(Port4)",
            autoneg="on",
            index="4",
            lanes="27",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth7(Port7)",
            autoneg="on",
            index="7",
            lanes="32",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth41(Port41)",
            autoneg="on",
            index="41",
            lanes="18",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth2(Port2)",
            autoneg="on",
            index="2",
            lanes="25",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="test",
        ),
        Port(
            admin_status="up",
            alias="Eth49(Port49)",
            autoneg="off",
            index="49",
            lanes="67",
            mtu="9100",
            speed="10000",
            oper_status="up",
            preemphasis="0x124106",
            description="DAR-01 Te1/0/6",
        ),
        Port(
            admin_status="down",
            alias="Eth33(Port33)",
            autoneg="on",
            index="33",
            lanes="10",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth24(Port24)",
            autoneg="on",
            index="24",
            lanes="43",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth54(Port54)",
            autoneg="off",
            index="54",
            lanes="69,70,71,72",
            mtu="9100",
            speed="100000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth32(Port32)",
            autoneg="on",
            index="32",
            lanes="7",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth42(Port42)",
            autoneg="on",
            index="42",
            lanes="17",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth25(Port25)",
            autoneg="on",
            index="25",
            lanes="2",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth11(Port11)",
            autoneg="on",
            index="11",
            lanes="40",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth8(Port8)",
            autoneg="on",
            index="8",
            lanes="31",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth22(Port22)",
            autoneg="on",
            index="22",
            lanes="41",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth46(Port46)",
            autoneg="on",
            index="46",
            lanes="21",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth18(Port18)",
            autoneg="on",
            index="18",
            lanes="45",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth15(Port15)",
            autoneg="on",
            index="15",
            lanes="36",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth20(Port20)",
            autoneg="on",
            index="20",
            lanes="47",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth37(Port37)",
            autoneg="on",
            index="37",
            lanes="14",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth52(Port52)",
            autoneg="off",
            index="52",
            lanes="68",
            mtu="9100",
            speed="10000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth14(Port14)",
            autoneg="on",
            index="14",
            lanes="33",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth29(Port29)",
            autoneg="on",
            index="29",
            lanes="6",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth27(Port27)",
            autoneg="on",
            index="27",
            lanes="4",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth28(Port28)",
            autoneg="on",
            index="28",
            lanes="3",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth10(Port10)",
            autoneg="on",
            index="10",
            lanes="37",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth38(Port38)",
            autoneg="on",
            index="38",
            lanes="13",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth36(Port36)",
            autoneg="on",
            index="36",
            lanes="11",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth12(Port12)",
            autoneg="on",
            index="12",
            lanes="39",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth48(Port48)",
            autoneg="on",
            index="48",
            lanes="23",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth53(Port53)",
            autoneg="off",
            index="53",
            lanes="73,74,75,76",
            mtu="9100",
            speed="100000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth21(Port21)",
            autoneg="on",
            index="21",
            lanes="42",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth45(Port45)",
            autoneg="on",
            index="45",
            lanes="22",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth6(Port6)",
            autoneg="on",
            index="6",
            lanes="29",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth13(Port13)",
            autoneg="on",
            index="13",
            lanes="34",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth17(Port17)",
            autoneg="on",
            index="17",
            lanes="46",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth26(Port26)",
            autoneg="on",
            index="26",
            lanes="1",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth43(Port43)",
            autoneg="on",
            index="43",
            lanes="20",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth3(Port3)",
            autoneg="on",
            index="3",
            lanes="28",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth51(Port51)",
            autoneg="off",
            index="51",
            lanes="65",
            mtu="9100",
            speed="10000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth1(Port1)",
            autoneg="on",
            index="1",
            lanes="26",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="yolo",
        ),
        Port(
            admin_status="down",
            alias="Eth30(Port30)",
            autoneg="on",
            index="30",
            lanes="5",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth40(Port40)",
            autoneg="on",
            index="40",
            lanes="15",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
        Port(
            admin_status="down",
            alias="Eth31(Port31)",
            autoneg="on",
            index="31",
            lanes="8",
            mtu="9100",
            speed="1000",
            oper_status="down",
            preemphasis="",
            description="",
        ),
    ]
)
lldp_neighbor_names = [
    lldp_entry.lldp_rem_sys_name for lldp_entry in lldp_entries.lldp_entries
]


if __name__ == "__main__":
    controller = Controller(
        Configuration(interval=1.0, screen=Screen.MAIN_VIEW, test=False)
    )
    controller.run()
