from sonic_cli.controller import Screen, Controller, Configuration, QueueMessage
from sonic_cli import SonicData
from sonic_cli.controller import display_to_screen, input_handler, MESSAGE_QUEUE
from unittest.mock import patch
import pytest
import signal
from sonic_cli.controller import signal_handler


@pytest.mark.parametrize(
    "user_input, expected_screen",
    [
        ("i", Screen.INTERFACE_VIEW),
        ("interface", Screen.INTERFACE_VIEW),
        ("m", Screen.MAIN_VIEW),
        ("main", Screen.MAIN_VIEW),
        ("l", Screen.LLDP_VIEW),
        ("lldp", Screen.LLDP_VIEW),
    ],
)
def test_input_handler_screen_change(user_input: str, expected_screen: Screen):
    # start with an empty queue:
    assert MESSAGE_QUEUE.empty()

    with patch("builtins.input", lambda *args: user_input):
        input_handler()

    assert (
        MESSAGE_QUEUE.empty() is False
    ), "Should have seen a message posted to the queue"
    message_from_queue = MESSAGE_QUEUE.get(1)
    assert message_from_queue.screen == expected_screen, "Did not read expected screen"


def test_input_handler_interval_changes():
    assert MESSAGE_QUEUE.empty()

    with patch("builtins.input", lambda *args: "1.2"):
        input_handler()

    assert (
        MESSAGE_QUEUE.empty() is False
    ), "Should have seen a message posted to the queue"
    message_from_queue = MESSAGE_QUEUE.get(1)
    assert message_from_queue.interval == 1.2
    with patch("builtins.input", lambda *args: "5.87"):
        input_handler()

    assert (
        MESSAGE_QUEUE.empty() is False
    ), "Should have seen a message posted to the queue"
    message_from_queue = MESSAGE_QUEUE.get(1)
    assert message_from_queue.interval == 5.87


def test_input_handler_invalid_input(capsys):
    assert MESSAGE_QUEUE.empty()

    with patch(
        "builtins.input",
        lambda *args: "this input message is unhandled and should result in a message to screen",
    ):
        input_handler()
    assert MESSAGE_QUEUE.empty()
    captured = capsys.readouterr()
    assert "valid input option." in captured.out


def test_input_handler_quit():
    assert MESSAGE_QUEUE.empty()
    with patch("builtins.input", lambda *args: "q"):
        with patch("os._exit") as mock_exit:
            input_handler()
    assert MESSAGE_QUEUE.empty()
    mock_exit.assert_called()


def test_display_to_screen(capsys):
    test_content = "Hello, World!"
    display_to_screen(test_content)
    captured = capsys.readouterr()
    assert test_content in captured.out


def test_display_empty_string(capsys):
    display_to_screen("")

    captured = capsys.readouterr()

    assert captured.out == "\x1b[2J\x1b[H\n"


def test_default_configuration(default_controller_config):
    assert isinstance(default_controller_config.sonic_data_retriever, SonicData)
    assert default_controller_config.interval == 1.0
    assert default_controller_config.screen == Screen.MAIN_VIEW


def test_controller_instantiation_with_defaults():
    controller = Controller()
    assert isinstance(controller.configuration.sonic_data_retriever, SonicData)
    assert controller.configuration.interval == 1.0
    assert controller.configuration.screen == Screen.MAIN_VIEW


def test_controller_view_main(sonic_data_testing_double):
    controller = Controller(
        Configuration(sonic_data_retriever=sonic_data_testing_double)
    )
    controller.display_screen(Screen.MAIN_VIEW)


def test_controller_view_interfaces(sonic_data_testing_double):
    controller = Controller(
        Configuration(sonic_data_retriever=sonic_data_testing_double)
    )
    controller.display_screen(Screen.INTERFACE_VIEW)


def test_controller_view_lldp(sonic_data_testing_double):
    controller = Controller(
        Configuration(sonic_data_retriever=sonic_data_testing_double)
    )
    controller.display_screen(Screen.LLDP_VIEW)


def test_signal_handler(monkeypatch, capsys):
    def mock_exit(code):
        """
        Mocks sys.exit and prevents the actual exit.
        """
        raise SystemExit(code)

    # set to use the mock:
    monkeypatch.setattr("sys.exit", mock_exit)

    # Send a SIGINT signal to trigger the signal_handler
    with pytest.raises(SystemExit) as excinfo:
        signal_handler(signal.SIGINT, None)

    captured = capsys.readouterr()
    assert "\nExiting..." in captured.out
    assert excinfo.value.code == 0


def test_controller_flip_screen(sonic_data_testing_double):
    controller = Controller(
        Configuration(sonic_data_retriever=sonic_data_testing_double)
    )
    assert MESSAGE_QUEUE.empty(), "should be empty at the start of the test"
    assert controller.configuration.interval == 1.0
    assert controller.configuration.screen == Screen.MAIN_VIEW
    # flip to LLDP:
    MESSAGE_QUEUE.put(QueueMessage(screen=Screen.LLDP_VIEW))
    controller.flip_screen_or_set_interval()
    assert controller.configuration.interval == 1.0
    assert controller.configuration.screen == Screen.LLDP_VIEW
    # change interval:
    MESSAGE_QUEUE.put(QueueMessage(interval=5.4))
    controller.flip_screen_or_set_interval()
    assert controller.configuration.interval == 5.4
    assert controller.configuration.screen == Screen.LLDP_VIEW
