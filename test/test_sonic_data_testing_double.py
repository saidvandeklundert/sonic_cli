from sonic_cli import Controller, Configuration
from sonic_cli.sonic_data_testing_double import SonicDataTestingDouble


def test_testing_double():
    controller = Controller(
        Configuration(
            sonic_data_retriever=SonicDataTestingDouble(),
        )
    )

    assert isinstance(controller, Controller)
    assert isinstance(
        controller.configuration.sonic_data_retriever, SonicDataTestingDouble
    )


def test_testing_double_meta_data():
    sonic_data_retriever = SonicDataTestingDouble()

    device_meta_data = sonic_data_retriever.get_config_device_metadata()
    assert device_meta_data.hostname == "CBS01"
    lldp_entries = sonic_data_retriever.get_all_lldp_entries()
    assert lldp_entries.lldp_entries
    software_information = sonic_data_retriever.get_software_version_information()
    assert software_information.software_version == "202211"
    all_ports = sonic_data_retriever.get_all_ports()
    assert all_ports.ports
    port_channel_state = sonic_data_retriever.get_port_channel_interfaces_status()
    assert port_channel_state.interfaces
