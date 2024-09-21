import pytest
from unittest.mock import patch
from sonic_cli.sonic_data import (
    SonicData,
    SonicDatabase,
    Port,
    Ports,
    LLDPEntry,
    LLDPEntries,
    ChassisInfo,
    DeviceMetaData,
)

# Mock data for testing
MOCK_PORT_DATA = {
    b"admin_status": b"up",
    b"alias": b"eth0",
    b"autoneg": b"on",
    b"index": b"1",
    b"lanes": b"65",
    b"mtu": b"9100",
    b"speed": b"100000",
    b"oper_status": b"up",
}

MOCK_LLDP_ENTRY_DATA = {
    b"lldp_rem_man_addr": b"00:00:00:00:00:01",
    b"lldp_rem_sys_cap_enabled": b"bridge, router",
    b"lldp_rem_index": b"1",
    b"lldp_rem_sys_desc": b"SONiC Software Version 1.0.0",
    b"lldp_rem_sys_cap_supported": b"bridge, router",
    b"lldp_rem_port_id": b"ethernet1",
    b"lldp_rem_sys_name": b"sonic-switch",
    b"lldp_rem_chassis_id": b"00:00:00:00:00:01",
    b"lldp_rem_port_desc": b"Ethernet1",
    b"lldp_rem_time_mark": b"1683554400",
    b"lldp_rem_chassis_id_subtype": b"4",
    b"lldp_rem_port_id_subtype": b"7",
}

MOCK_CHASSIS_INFO_DATA = {
    b"serial": b"ABC123",
    b"model": b"SuperSwitch",
    b"revision": b"1.0",
    b"psu_num": b"2",
}

MOCK_DEVICE_METADATA_DATA = {
    b"buffer_model": b"traditional",
    b"default_bgp_status": b"up",
    b"default_pfcwd_status": b"disable",
    b"hostname": b"sonic-switch",
    b"hwsku": b"SuperSwitch",
    b"platform": b"x86_64-sonic_debian10-r0",
    b"mac": b"00:00:00:00:00:01",
    b"synchronous_mode": b"enable",
    b"type": b"ToRRouter",
}


@pytest.fixture
def sonic_data():
    return SonicData()


@patch("sonic_cli.sonic_data.redis.Redis")
def test_get_port(mock_redis, sonic_data):
    mock_redis_instance = mock_redis.return_value
    mock_redis_instance.hgetall.return_value = MOCK_PORT_DATA

    port = sonic_data.get_port(key="PORT_TABLE:Ethernet1")
    assert isinstance(port, Port)
    assert port.admin_status == MOCK_PORT_DATA[b"admin_status"].decode("utf-8")
    assert port.alias == MOCK_PORT_DATA[b"alias"].decode("utf-8")


@patch("sonic_cli.sonic_data.redis.Redis")
def test_get_all_ports(mock_redis, sonic_data):
    mock_redis_instance = mock_redis.return_value
    mock_redis_instance.scan.return_value = (
        0,
        [b"PORT_TABLE:Ethernet1", b"PORT_TABLE:Ethernet2"],
    )
    mock_redis_instance.hgetall.return_value = MOCK_PORT_DATA

    ports = sonic_data.get_all_ports()
    assert isinstance(ports, Ports)
    assert len(ports.ports) == 2
    for port in ports.ports:
        assert isinstance(port, Port)
        assert port.admin_status == MOCK_PORT_DATA[b"admin_status"].decode("utf-8")
        assert port.alias == MOCK_PORT_DATA[b"alias"].decode("utf-8")


@patch("sonic_cli.sonic_data.redis.Redis")
def test_get_lldp_entry(mock_redis, sonic_data):
    mock_redis_instance = mock_redis.return_value
    mock_redis_instance.hgetall.return_value = MOCK_LLDP_ENTRY_DATA

    lldp_entry = sonic_data.get_lldp_entry(key="LLDP_ENTRY_TABLE:Ethernet1")
    assert isinstance(lldp_entry, LLDPEntry)
    assert lldp_entry.lldp_rem_man_addr == MOCK_LLDP_ENTRY_DATA[
        b"lldp_rem_man_addr"
    ].decode("utf-8")
    assert lldp_entry.lldp_rem_sys_cap_enabled == MOCK_LLDP_ENTRY_DATA[
        b"lldp_rem_sys_cap_enabled"
    ].decode("utf-8")


@patch("sonic_cli.sonic_data.redis.Redis")
def test_get_all_lldp_entries(mock_redis, sonic_data):
    mock_redis_instance = mock_redis.return_value
    mock_redis_instance.scan.return_value = (
        0,
        [b"LLDP_ENTRY_TABLE:Ethernet1", b"LLDP_ENTRY_TABLE:Ethernet2"],
    )
    mock_redis_instance.hgetall.return_value = MOCK_LLDP_ENTRY_DATA

    lldp_entries = sonic_data.get_all_lldp_entries()
    assert isinstance(lldp_entries, LLDPEntries)
    assert len(lldp_entries.lldp_entries) == 2
    for lldp_entry in lldp_entries.lldp_entries:
        assert isinstance(lldp_entry, LLDPEntry)
        assert lldp_entry.lldp_rem_man_addr == MOCK_LLDP_ENTRY_DATA[
            b"lldp_rem_man_addr"
        ].decode("utf-8")
        assert lldp_entry.lldp_rem_sys_cap_enabled == MOCK_LLDP_ENTRY_DATA[
            b"lldp_rem_sys_cap_enabled"
        ].decode("utf-8")


@patch("sonic_cli.sonic_data.redis.Redis")
def test_get_chassis_information(mock_redis, sonic_data):
    mock_redis_instance = mock_redis.return_value
    mock_redis_instance.scan.return_value = (0, [b"CHASSIS_INFO|chassis"])
    mock_redis_instance.hgetall.return_value = MOCK_CHASSIS_INFO_DATA

    chassis_info = sonic_data.get_chassis_information()
    assert isinstance(chassis_info, list)
    assert len(chassis_info) == 1
    assert isinstance(chassis_info[0], ChassisInfo)
    assert chassis_info[0].serial == MOCK_CHASSIS_INFO_DATA[b"serial"].decode("utf-8")
    assert chassis_info[0].model == MOCK_CHASSIS_INFO_DATA[b"model"].decode("utf-8")
    assert chassis_info[0].revision == MOCK_CHASSIS_INFO_DATA[b"revision"].decode(
        "utf-8"
    )
    assert chassis_info[0].psu_num == MOCK_CHASSIS_INFO_DATA[b"psu_num"].decode("utf-8")


@patch("sonic_cli.sonic_data.redis.Redis")
def test_get_config_device_metadata(mock_redis, sonic_data):
    mock_redis_instance = mock_redis.return_value
    mock_redis_instance.hgetall.return_value = MOCK_DEVICE_METADATA_DATA

    device_metadata = sonic_data.get_config_device_metadata()
    assert isinstance(device_metadata, DeviceMetaData)
    assert device_metadata.buffer_model == MOCK_DEVICE_METADATA_DATA[
        b"buffer_model"
    ].decode("utf-8")
    assert device_metadata.default_bgp_status == MOCK_DEVICE_METADATA_DATA[
        b"default_bgp_status"
    ].decode("utf-8")
    assert device_metadata.default_pfcwd_status == MOCK_DEVICE_METADATA_DATA[
        b"default_pfcwd_status"
    ].decode("utf-8")
    assert device_metadata.hostname == MOCK_DEVICE_METADATA_DATA[b"hostname"].decode(
        "utf-8"
    )
    assert device_metadata.hwsku == MOCK_DEVICE_METADATA_DATA[b"hwsku"].decode("utf-8")
    assert device_metadata.platform == MOCK_DEVICE_METADATA_DATA[b"platform"].decode(
        "utf-8"
    )
    assert device_metadata.mac == MOCK_DEVICE_METADATA_DATA[b"mac"].decode("utf-8")
    assert device_metadata.synchronous_mode == MOCK_DEVICE_METADATA_DATA[
        b"synchronous_mode"
    ].decode("utf-8")
    assert device_metadata.type == MOCK_DEVICE_METADATA_DATA[b"type"].decode("utf-8")


def test_sonic_database():
    assert SonicDatabase.APLL_DB.value == 0
    assert SonicDatabase.ASIC_DB.value == 1
    assert SonicDatabase.COUNTERS_DB.value == 2
    assert SonicDatabase.LOGLEVEL_DB.value == 3
    assert SonicDatabase.CONFIG_DB.value == 4
    assert SonicDatabase.FLEX_COUNTER_DB.value == 5
    assert SonicDatabase.STATE_DB.value == 6
