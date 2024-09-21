from sonic_cli.controller import Screen, Controller, Configuration
from sonic_cli import SonicData
from sonic_cli.controller import display_to_screen


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

# test_signal_handler.py
import pytest
import signal
from sonic_cli.controller import signal_handler

def test_signal_handler(monkeypatch, capsys):
    
    def mock_exit(code):
        """
        Mocks sys.exit and prevents the actual exit.
        """
        raise SystemExit(code)
    
    # set to use the mock:
    monkeypatch.setattr('sys.exit', mock_exit)
    
    # Send a SIGINT signal to trigger the signal_handler
    with pytest.raises(SystemExit) as excinfo:
        signal_handler(signal.SIGINT, None)
    
 
    captured = capsys.readouterr()
    assert "\nExiting..." in captured.out
    assert excinfo.value.code == 0
