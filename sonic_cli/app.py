from sonic_cli import Configuration, Controller, Screen
from sonic_cli.sonic_data import SonicData


def monitor(configuration: Configuration) -> None:
    """
    Run the monitor_device program.

    Calling example:

    >>> monitor(configuration=Configuration())
    """
    controller = Controller(configuration=configuration)

    controller.run()
