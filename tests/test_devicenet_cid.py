import pytest

from devicenet.cid import DeviceNetCID
from devicenet.enums import DeviceNetMessageGroup


def test_devicenetcid_pack():
    cid = DeviceNetCID(
        message_group=DeviceNetMessageGroup.MESSAGE_GROUP_1, message_id=0x4, mac_id=0x16
    )
    assert cid.pack() == 0x116

    cid = DeviceNetCID(
        message_group=DeviceNetMessageGroup.MESSAGE_GROUP_2, message_id=0x6, mac_id=0x38
    )
    assert cid.pack() == 0x5C6

    cid = DeviceNetCID(
        message_group=DeviceNetMessageGroup.MESSAGE_GROUP_3, message_id=0x6, mac_id=0x38
    )
    assert cid.pack() == 0x7B8

    cid = DeviceNetCID(
        message_group=DeviceNetMessageGroup.MESSAGE_GROUP_4, message_id=0x15
    )
    assert cid.pack() == 0x7D5


def test_devicenetcid_unpack():
    cid = DeviceNetCID.unpack(0x1FF)
    assert cid.message_group == DeviceNetMessageGroup.MESSAGE_GROUP_1
    assert cid.message_id == 0b0111
    assert cid.mac_id == 0b111111

    cid = DeviceNetCID.unpack(0x499)
    assert cid.message_group == DeviceNetMessageGroup.MESSAGE_GROUP_2
    assert cid.message_id == 0b001
    assert cid.mac_id == 0b010011

    cid = DeviceNetCID.unpack(0x709)
    assert cid.message_group == DeviceNetMessageGroup.MESSAGE_GROUP_3
    assert cid.message_id == 0b100
    assert cid.mac_id == 0b0001001

    cid = DeviceNetCID.unpack(0x7D4)
    assert cid.message_group == DeviceNetMessageGroup.MESSAGE_GROUP_4
    assert cid.message_id == 0b010100
    assert cid.mac_id is None


@pytest.mark.parametrize(
    ("function", "mac", "expected_cid"),
    [
        ("slave_multicast_poll_response", 0x07, 0x307),
        ("slave_change_of_state_or_cyclic", 0x31, 0x371),
        ("slave_bit_strobe_response", 0x23, 0x3A3),
        ("slave_poll_response_or_ack", 0x2A, 0x3EA),
        ("master_bit_strobe_command", 0x2A, 0x550),
        ("master_multicast_poll", 0x15, 0x4A9),
        ("master_change_of_state_or_cyclic_ack", 0x1F, 0x4FA),
        ("slave_explicit_response", 0x00, 0x403),
        ("master_explicit_request", 0x01, 0x40C),
        ("master_poll_command_or_change_of_state_or_cyclic", 0x21, 0x50D),
        ("group_2_unconnected_explicit_request", 0x31, 0x58E),
        ("duplicate_mac_id_check", 0x35, 0x5AF),
    ],
)
def test_predefined_cid(function, mac, expected_cid):
    cid = getattr(DeviceNetCID, function)(mac)
    assert cid.pack() == expected_cid
