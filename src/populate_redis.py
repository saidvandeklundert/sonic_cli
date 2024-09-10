import redis
from dataclasses import asdict
from models import Port, SonicDataRetriever, LLDPEntry
import random

# Create a Redis client
redis_client = redis.Redis(host="localhost", port=6379, db=0)

ports = [
    "1",
    "2",
    "3",
    "4",
    "10",
    "12",
    "21",
    "22",
    "24",
    "27",
    "28",
    "31",
    "34",
    "48",
    "49",
]
if __name__ == "__main__":
    for port in ports:
        one_or_two = random.randint(1, 2)
        admin_status = "up" if one_or_two == 1 else "down"
        oper_status = "down" if admin_status == "down" else "up"
        # Create a Port instance
        port_value = Port(
            admin_status=admin_status,
            alias=f"Eth{port}",
            autoneg="on",
            index="1",
            lanes="3",
            mtu="9100",
            speed="1000",
            description=f"Ethernet{port}",
            oper_status=oper_status,
            preemphasis="high",
        )

        # Convert the Port instance to a dictionary
        port_value_dict = asdict(port_value)

        # Store the nested structure as a hash in Redis
        key = f"PORT_TABLE:Ethernet{port}"
        redis_client.hset(key, mapping=port_value_dict)

        print(f"Stored Port for {key} in Redis")
    entry_1 = LLDPEntry(
        lldp_rem_man_addr="7.32.1.40,2605:b140:100:1001::d:1",
        lldp_rem_sys_cap_enabled="28 00",
        lldp_rem_index="4",
        lldp_rem_sys_desc="Cisco IOS Software [Amsterdam], Catalyst L3 Switch Software (CAT9K_IOSXE), Version 17.3.3, RELEASE SOFTWARE (fc7)\nTechnical Support: http://www.cisco.com/techsupport\nCopyright (c) 1986-2021 by Cisco Systems, Inc.\nCompiled Thu 04-Mar-21 12:32 by mcpre",
        lldp_rem_sys_cap_supported="28 00",
        lldp_rem_port_id="Te2/0/6",
        lldp_rem_sys_name="dev-1.ffnx.int",
        lldp_rem_chassis_id="7c:ad:4f:b1:15:00",
        lldp_rem_port_desc="",
        lldp_rem_time_mark="1355128",
        lldp_rem_chassis_id_subtype="4",
        lldp_rem_port_id_subtype="5",
    )

    entry_2 = LLDPEntry(
        lldp_rem_man_addr="7.32.1.40,2605:b140:100:1001::d:1",
        lldp_rem_sys_cap_enabled="28 00",
        lldp_rem_index="4",
        lldp_rem_sys_desc="Cisco IOS Software [Amsterdam], Catalyst L3 Switch Software (CAT9K_IOSXE), Version 17.3.3, RELEASE SOFTWARE (fc7)\nTechnical Support: http://www.cisco.com/techsupport\nCopyright (c) 1986-2021 by Cisco Systems, Inc.\nCompiled Thu 04-Mar-21 12:32 by mcpre",
        lldp_rem_sys_cap_supported="28 00",
        lldp_rem_port_id="Te1/0/6",
        lldp_rem_sys_name="dev-1.ffnx.int",
        lldp_rem_chassis_id="7c:ad:4f:b1:15:00",
        lldp_rem_port_desc="",
        lldp_rem_time_mark="1315040",
        lldp_rem_chassis_id_subtype="4",
        lldp_rem_port_id_subtype="5",
    )
    sdr = SonicDataRetriever()
    sdr.store_lldp_entry(entry_1, "Ethernet49")
    sdr.store_lldp_entry(entry_2, "Ethernet48")
