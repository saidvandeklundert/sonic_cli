import threading
from sonic_cli import Screen
from sonic_cli.sonic_data import *
from sonic_cli.view import view_builder
from sonic_cli.data_models import data_model_builder
import time
import queue
import sys
import os
import signal


class Instruction(Enum):
    SET_SCREEN = "set_screen"
    SET_INTERVAL = "set_interval"


@dataclass
class QueueMessage:
    """
    Message used to signal the app to change behavior or change the view.
    """

    instruction: Optional[Instruction] = None
    interval: Optional[float] = None
    screen: Optional[Screen] = None


MESSAGE_QUEUE: queue.Queue[QueueMessage] = queue.Queue()


def display_to_screen(content: str) -> None:
    # clear screen:
    sys.stdout.write("\033[2J")
    # cursor to (0, 0)
    sys.stdout.write("\033[H")
    print(content)
    sys.stdout.flush()


def signal_handler(signal, frame):
    """Handles the signal for graceful exit."""
    print("\nExiting...")
    sys.exit(0)


# Register the signal handler for SIGINT (Ctrl+C)
signal.signal(signal.SIGINT, signal_handler)


def input_handler():
    """
    Posts a QueueMessage based on the input that is read.
    """
    line = input()
    if len(line) >= 1 and line[0].isdigit():
        new_interval = float(line)
        MESSAGE_QUEUE.put(QueueMessage(interval=new_interval))
        print("change interval")
    elif line.lower() == "i" or line == "interface":
        MESSAGE_QUEUE.put(QueueMessage(screen=Screen.INTERFACE_VIEW))
        print("change to interface view")
    elif line.lower() == "m" or line == "main":
        MESSAGE_QUEUE.put(QueueMessage(screen=Screen.MAIN_VIEW))
        print("change to main view")
    elif line.lower() == "l" or line == "lldp":
        MESSAGE_QUEUE.put(QueueMessage(screen=Screen.LLDP_VIEW))
        print("change to main view")
    elif line.lower() == "q":
        print("\nExiting...")
        os._exit(0)
    else:
        print(f"{line} is not a valid input option.")
    print(f"selection input: {line}")


def input_thread_function():
    """
    Thread that constantly listens for user input.

    Halts the program , flips the view, etc.
    """
    try:
        while True:
            input_handler()
    except Exception as err:
        print(err)


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
        display_to_screen(view.render())

    def flip_screen_or_set_interval(self) -> None:
        """
        Communicate to the input thread and:
        - instruct the view to change
        - change the interval at which the program runs
        """
        if not MESSAGE_QUEUE.empty():
            message_from_queue = MESSAGE_QUEUE.get(1)
            if isinstance(message_from_queue, QueueMessage):
                if message_from_queue.screen is not None:
                    self.configuration.screen = message_from_queue.screen
                if message_from_queue.interval is not None:
                    self.configuration.interval = message_from_queue.interval

    def run(self) -> None:
        """
        Run the application.

        Starts an input thread that listens for user input and runs the rest of the
         program under the main thread.
        """
        input_thread = threading.Thread(target=input_thread_function)
        input_thread.daemon = True
        input_thread.start()
        try:
            while True:
                self.flip_screen_or_set_interval()
                interval = self.configuration.interval
                screen_value = self.configuration.screen
                time.sleep(interval)
                self.display_screen(screen=screen_value)
                # columns, lines = shutil.get_terminal_size()
        except KeyboardInterrupt:  # Handles 'Ctrl+C'
            print("\nExiting monitor tool...")
