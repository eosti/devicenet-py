from devicenet.enums import DeviceNetFragmentationType
from devicenet.fields import (
    DeviceNetExplicitHeader,
    DeviceNetFragmentProtocol,
    DeviceNetServiceField,
)


def test_devicenet_explicit_header():
    field = DeviceNetExplicitHeader(mac_id=0x04, frag=False, xid=False)
    assert field.pack() == bytes([0x04])
    assert DeviceNetExplicitHeader.unpack(bytes([0x04])) == field

    field = DeviceNetExplicitHeader(mac_id=0x35, frag=True, xid=True)
    assert field.pack() == bytes([0xF5])
    assert DeviceNetExplicitHeader.unpack(bytes([0xF5])) == field

    field = DeviceNetExplicitHeader(mac_id=0x04, frag=False, xid=True)
    assert field.pack() == bytes([0x44])
    assert DeviceNetExplicitHeader.unpack(bytes([0x44])) == field

    field = DeviceNetExplicitHeader(mac_id=0x04, frag=True, xid=False)
    assert field.pack() == bytes([0x84])
    assert DeviceNetExplicitHeader.unpack(bytes([0x84])) == field


def test_devicenet_service_field():
    field = DeviceNetServiceField(service_code=0x49, is_response=False)
    assert field.pack() == bytes([0x49])
    assert DeviceNetServiceField.unpack(bytes([0x49])) == field

    field = DeviceNetServiceField(service_code=0x49, is_response=True)
    assert field.pack() == bytes([0xC9])
    assert DeviceNetServiceField.unpack(bytes([0xC9])) == field


def test_devicenet_fragment_protocol():
    field = DeviceNetFragmentProtocol(
        fragment_type=DeviceNetFragmentationType.FIRST_FRAGMENT,
        fragmentation_count=0x00,
    )
    assert field.pack() == bytes([0x00])
    assert DeviceNetFragmentProtocol.unpack(bytes([0x00])) == field

    field = DeviceNetFragmentProtocol(
        fragment_type=DeviceNetFragmentationType.MIDDLE_FRAGMENT,
        fragmentation_count=0x07,
    )
    assert field.pack() == bytes([0x47])
    assert DeviceNetFragmentProtocol.unpack(bytes([0x47])) == field

    field = DeviceNetFragmentProtocol(
        fragment_type=DeviceNetFragmentationType.LAST_FRAGMENT, fragmentation_count=0x1A
    )
    assert field.pack() == bytes([0x9A])
    assert DeviceNetFragmentProtocol.unpack(bytes([0x9A])) == field

    field = DeviceNetFragmentProtocol(
        fragment_type=DeviceNetFragmentationType.FRAGMENT_ACKNOWLEDGE,
        fragmentation_count=0x04,
    )
    assert field.pack() == bytes([0xC4])
    assert DeviceNetFragmentProtocol.unpack(bytes([0xC4])) == field
