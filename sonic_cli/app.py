from sonic_cli import Configuration, Controller


def monitor(configuration: Configuration) -> None:
    """
    Run the monitor_device program.

    Calling example:

    >>> monitor(configuration=Configuration())
    """
    controller = Controller(configuration=configuration)

    controller.run()
