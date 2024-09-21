from __future__ import annotations
from dataclasses import dataclass
from typing import Union
from enum import Enum
from sonic_cli.sonic_data import *
from typing import List


class Screen(str, Enum):
    """
    THe different screens available for selection.
    """

    MAIN_VIEW = "main"
    INTERFACE_VIEW = "interface"
    LLDP_VIEW = "lldp"


@dataclass
class UserScreen:
    screen_lines: ScreenList


@dataclass
class TerminalSize:
    """
    The terminal size. The lines indicate the height of the screen and the columns
     indicate the width.
    """

    columns: int
    lines: int


class ScreenList(list):
    """
    Wrapper class around a list.

    This allows us to easily add lines to a sreen that are colored.
    """

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
    screen: Screen = Screen.MAIN_VIEW, sd: SonicData = SonicData()
) -> ScreenData:
    """
    Returnes a data model to seed one of the 'Screen' types that are supported.
    """
    builder_data = {
        "main": main_view_model_builder,
        "interface": interface_view_model_builder,
        "lldp": lldp_view_model_builder,
    }
    return builder_data[screen.value](sd)


def main_view_model_builder(sd: SonicData) -> MainViewData:
    """
    Builds the model that allows for the rendering
     of the main view.

    When test is set to True, the model data is seeded from a constant
    """
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


def interface_view_model_builder(sd: SonicData) -> InterfaceViewData:
    """
    Builds the model that allows for the rendering
     of the interface view.
    """
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


def lldp_view_model_builder(sd: SonicData) -> LldpViewData:
    """
    Builds the model that allows for the rendering
     of the lldp view.
    """
    retrieved_meta_data = sd.get_config_device_metadata()
    retrieved_lldp_entries = sd.get_all_lldp_entries()
    retrieved_software_information = sd.get_software_version_information()
    return LldpViewData(
        hostname=retrieved_meta_data.hostname,
        model=retrieved_meta_data.hwsku,
        software_version=retrieved_software_information.software_version,
        neighbors=retrieved_lldp_entries,
    )
