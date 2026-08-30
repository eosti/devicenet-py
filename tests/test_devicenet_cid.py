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
