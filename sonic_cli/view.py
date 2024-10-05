#!/usr/bin/env python
from __future__ import annotations
import shutil
from sonic_cli import Screen, ScreenList, TerminalSize
from abc import abstractmethod, ABC
import shutil
import datetime
from sonic_cli import (
    Screen,
    ScreenList,
    TerminalSize,
    MainViewData,
    LldpViewData,
    InterfaceViewData,
    ViewData,
)


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
        user_screen.append_light_yellow(
            f"System model:".ljust(30) + f"{self.data.model}"
        )
        user_screen.append_light_yellow(
            f"System version:".ljust(30) + f"{self.data.software_version}"
        )
        user_screen.append_light_yellow(
            f"Kernel version:".ljust(30) + f"{self.data.kernel_version}"
        )
        user_screen.append_yellow(self.section_separator())
        for cpu in self.data.cpu_usage.cpu_cores:
            user_screen.append_light_yellow(f"CPU {cpu.number} is using {cpu.usage}%")
        user_screen.append_yellow(self.section_separator())
        user_screen.append_light_yellow(
            f"CPU usage average 1 min:".ljust(30)
            + f"{self.data.cpu_usage.average_usage_last_minute}"
        )
        user_screen.append_light_yellow(
            f"CPU usage average 5 min:".ljust(30)
            + f"{self.data.cpu_usage.average_usage_last_5_minutes}"
        )
        user_screen.append_light_yellow(
            f"CPU usage average 15 min:".ljust(30)
            + f"{self.data.cpu_usage.average_usage_last_15_minutes}"
        )
        user_screen.append_yellow(self.section_separator())

        user_screen.append_light_yellow(
            f"Memory total in GB:".ljust(30)
            + f"{self.data.memory_usage.total_memory_in_gb}"
        )
        user_screen.append_light_yellow(
            f"Memory available in GB:".ljust(30)
            + f"{self.data.memory_usage.available_memory_in_gb} ( {100 - self.data.memory_usage.percent:.1f}% )"
        )
        user_screen.append_light_yellow(
            f"Memory used in GB:".ljust(30)
            + f"{self.data.memory_usage.used_memory_in_gb} ( {self.data.memory_usage.percent:.1f}% )"
        )

        user_screen.append_yellow(self.section_separator())
        user_screen.append_light_yellow(
            f"Detected LLDP neighbors:".ljust(30) + f"{len(self.data.lldp_neighbors)}"
        )

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
        user_screen.append_gold(
            f"Port information (includes admin enabled interfaces only):"
        )
        user_screen.append_light_yellow(self.sub_section_separator())
        user_screen.append_light_yellow(
            f"{'Port name':<25} | {'admin status':<15} | {'operational status':<20} | {'description':<20}"
        )

        for interface in self.data.ports.ports:
            if interface.admin_status == "up":
                description = interface.description if interface.description else ""
                line = f"{interface.alias:<25} | {interface.admin_status:<15} | {interface.oper_status:<20} | {description:<20}"
                if interface.oper_status == "up":
                    user_screen.append_gold(line)
                else:
                    user_screen.append_red(line)

        user_screen.append_light_yellow(self.sub_section_separator())
        user_screen.append_gold(f"Interfaces attached to a port channel:")
        user_screen.append_light_yellow(self.sub_section_separator())
        user_screen.append_light_yellow(
            f"{'Port channel name':<25} | {'port channel status':<25} | {'child interface':<20}"
        )
        for int_name, port_channel_state in self.data.port_channels.interfaces.items():
            user_screen.append_gold(
                f"{port_channel_state.port_channel_name:<25} | {port_channel_state.status:<25} | {int_name:<20}"
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
        user_screen.append_light_yellow(f"Known LLDP neighbors:")
        user_screen.append_light_yellow(self.sub_section_separator())
        user_screen.append_gold(
            f"{'Sytem name':<45} | {'local port':<20} | {'remote port':<20}"
        )
        for neighbor in self.data.neighbors.lldp_entries:
            user_screen.append_light_yellow(self.sub_section_separator())
            user_screen.append_light_yellow(
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
