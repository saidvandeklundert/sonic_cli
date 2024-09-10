import time
import sys
import os
import signal
import threading
from models import Screen
from build_message import build_message
import queue

message_queue = queue.Queue()
REFRESH_RATE_IN_SECONDS = 0.4  # float that determines how often a new screen is built


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


def input_thread():
    """
    Thread that constantly listens for user input.

    Either halts the program or uses a message queue to flip the view.
    """
    while True:
        line = sys.stdin.read(1)
        if line == "q":
            print("\nExiting...")
            os._exit(0)  # Exit the entire process
        elif line == "i" or line == "interface":
            message_queue.put(Screen.INTERFACES)
            print("change to interface view")
        elif line == "m" or line == "main":
            message_queue.put(Screen.MAIN)
            print("change to main view")
        elif line == "l" or line == "lldp":
            message_queue.put(Screen.LLDP)
            print("change to main view")


try:
    counter = 0
    input_thread = threading.Thread(target=input_thread)
    input_thread.daemon = True  # Allow the thread to exit when the main program exits
    input_thread.start()
    instruction = Screen.MAIN
    while True:
        if not message_queue.empty():
            message_from_queue = message_queue.get(1)
            print(message_from_queue)
            instruction = message_from_queue
        message = build_message(message=instruction)
        display_message(message)

        counter += 1

        # Wait for 2 seconds
        for _ in range(2):
            time.sleep(REFRESH_RATE_IN_SECONDS)

except KeyboardInterrupt:
    # Handle the KeyboardInterrupt exception (Ctrl+C)
    print("\nExiting...")
