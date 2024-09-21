from sonic_cli import monitor

import pytest
from unittest import mock
from sonic_cli import Configuration, Controller, Screen
from sonic_cli.sonic_data import SonicData
from sonic_cli.sonic_data_testing_double import SonicDataTestingDouble

from sonic_cli import monitor


@mock.patch("sonic_cli.controller.Controller.run")
def test_monitor(mocked_controller):
    mocked_controller.run.return_value = "OK"
    configuration = Configuration(sonic_data_retriever=SonicDataTestingDouble())
    monitor(configuration=configuration)
