import pytest
from sonic_cli import Configuration
from sonic_cli.sonic_data_testing_double import SonicDataTestingDouble


@pytest.fixture
def sonic_data_testing_double() -> SonicDataTestingDouble:
    sonic_data_retriever = SonicDataTestingDouble()
    return sonic_data_retriever


@pytest.fixture
def default_controller_config():
    """
    Returns a default configuration for a Controller instance
    """
    return Configuration()
