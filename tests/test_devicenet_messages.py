from devicenet.enums import DeviceNetBodyFormat, DeviceNetMessageGroup
from devicenet.messages import (
    DeviceNetExplicitMessage,
    DeviceNetExplicitMessageGenericService,
    DeviceNetExplicitMessagingConnectionRequestMessage,
    DeviceNetExplicitMessagingConnectionResponseMessage,
)


def test_devicenet_explicit_message():
    msg = DeviceNetExplicitMessage(mac_id=0x04, message=bytes([0xA4, 0x4B]))
    assert next(msg.pack()) == bytes([0x04, 0xA4, 0x4B])
    assert DeviceNetExplicitMessage.unpack(bytes([0x04, 0xA4, 0x4B])) == msg

    msg = DeviceNetExplicitMessage(
        mac_id=0x08, message=bytes([0xA4, 0x4B, 0x04, 0x05, 0x06, 0x07]), xid=True
    )
    assert next(msg.pack()) == bytes([0x48, 0xA4, 0x4B, 0x04, 0x05, 0x06, 0x07])
    assert DeviceNetExplicitMessage.unpack(bytes([0x48, 0xA4, 0x4B, 0x04, 0x05, 0x06, 0x07])) == msg


def test_devicenet_explicit_fragmented_message():
    # TODO: more fragment tests
    msg = DeviceNetExplicitMessage(
        mac_id=0x08, message=bytes([0xA4, 0x4B, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06])
    )
    raw = msg.pack()
    assert next(raw) == bytes([0x88, 0x00, 0xA4, 0x4B, 0x01, 0x02, 0x03, 0x04])
    assert next(raw) == bytes([0x88, 0x81, 0x05, 0x06])
    assert (
        DeviceNetExplicitMessage.unpack(
            [
                bytes([0x88, 0x00, 0xA4, 0x4B, 0x01, 0x02, 0x03, 0x04]),
                bytes([0x88, 0x81, 0x05, 0x06]),
            ]
        )
        == msg
    )


def test_devicenet_explicit_message_generic_service():
    msg = DeviceNetExplicitMessageGenericService(
        mac_id=0x04, service_code=0x4B, message=bytes([0xA4, 0x4B])
    )
    assert next(msg.pack()) == bytes([0x04, 0x4B, 0xA4, 0x4B])
    assert DeviceNetExplicitMessageGenericService.unpack(bytes([0x04, 0x4B, 0xA4, 0x4B])) == msg


def test_devicenet_connection_request_message():
    msg = DeviceNetExplicitMessagingConnectionRequestMessage(
        dest_mac=0x07,
        body_format=DeviceNetBodyFormat.DEVICENET_8_8,
        group_select=DeviceNetMessageGroup.MESSAGE_GROUP_2,
        source_message_id=0x7,
    )
    assert next(msg.pack()) == bytes([0x07, 0x4B, 0x00, 0x17])
    assert (
        DeviceNetExplicitMessagingConnectionRequestMessage.unpack(bytes([0x07, 0x4B, 0x00, 0x17]))
        == msg
    )


def test_devicenet_connection_response_message():
    msg = DeviceNetExplicitMessagingConnectionResponseMessage(
        dest_mac=0x07,
        body_format=DeviceNetBodyFormat.DEVICENET_8_8,
        destination_message_id=0x3,
        source_message_id=0x7,
        connection_instance_id=0x4701,
    )
    assert next(msg.pack()) == bytes([0x07, 0xCB, 0x00, 0x37, 0x01, 0x47])
    assert (
        DeviceNetExplicitMessagingConnectionResponseMessage.unpack(
            bytes([0x07, 0xCB, 0x00, 0x37, 0x01, 0x47])
        )
        == msg
    )
