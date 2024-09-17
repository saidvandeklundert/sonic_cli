import threading
from monitor_device import Screen
from monitor_device.sonic_data import *
from monitor_device.view import view_builder
from monitor_device.data_models import data_model_builder
import shutil
import time
from typing import Tuple, Union
import queue
import sys
import os
import signal

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
        if len(line) >= 1 and line[0].isdigit():
            new_interval = float(line)
            message_queue.put(new_interval)
            print("change interval")
        elif line.lower() == "q":
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
        else:
            print(f"{line} is not a valid input option.")
        print(f"selection input: {line}")


@dataclass
class Configuration:
    """
    Program configuration with sensible defaults.

    interval: refresh rate of the program.
    screen: determines what view should be presented to the user.
    test: should be set to False in case the program is running
     on the device, set it to True otehrwise.
    """

    sonic_data_retriever: SonicData = SonicData()
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
        data = data_model_builder(screen, self.configuration.sonic_data_retriever)
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
        except KeyboardInterrupt:
            # Handle the KeyboardInterrupt exception (Ctrl+C)
            print("\nExiting monitor tool...")
