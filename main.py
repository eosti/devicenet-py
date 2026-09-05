import logging
import sys

from bitstring import Bits
from can.interface import Bus

from devicenet.devicenet import DeviceNet
from devicenet.enums import (
    DeviceNetBodyFormat,
    DeviceNetConnectionObjectAttributes,
    DeviceNetMessageGroup,
)
from devicenet.fields import DeviceNetAllocationChoiceByte


def main():
    logging.basicConfig(level=logging.DEBUG)

    bus = Bus(
        interface="slcan", channel="/dev/tty.usbmodem2086346F47431", bitrate=250000
    )
    dn = DeviceNet(bus, 0x7, vendor_id=0x0102, serial_number=0x0F0A0077)
    dn.connect(quick_connect=True)

    allocation_choice = DeviceNetAllocationChoiceByte(polled=True, change_of_state=True)

    dn.master_slave_connect(dest_mac_id=0x03, allocation_choice=allocation_choice)

    for a in DeviceNetConnectionObjectAttributes:
        try:
            attr = dn.get_attribute_single(dest_mac_id=0x03, attribute=a)
            print(f"{a.name}: {attr}")
        except RuntimeError:
            print(f"{a.name}: Not Supported")

    dn.set_attribute_single(
        dest_mac_id=0x03,
        attribute=DeviceNetConnectionObjectAttributes.EXPECTED_PACKET_RATE,
        val=2500,
    )

    attr = dn.get_attribute_single(
        dest_mac_id=0x03,
        attribute=DeviceNetConnectionObjectAttributes.EXPECTED_PACKET_RATE,
    )
    print(f"epr: : {attr}")

    for i in range(16):
        if i == 0:
            # buzzer bypass
            continue
        bitfield = (0b1 << i).to_bytes(2, "big", signed=False)
        dn.poll_io(dest_mac_id=0x03, val=bitfield)
        input("enter to continue...")

    while 1:
        print(Bits(dn.poll_io(dest_mac_id=0x03)).bin)
        dn.handle_messages()

    sys.exit(1)
    for addr in range(0x3F + 1):
        if addr == 0x03:
            continue
        bus = Bus(
            interface="slcan", channel="/dev/tty.usbmodem2086346F47431", bitrate=250000
        )
        dn = DeviceNet(bus, addr, vendor_id=0x0102, serial_number=0x0F0A0077)
        dn.connect(quick_connect=True)
        dn.open_explicit_messaging_connection_request(
            dest_mac_id=0x3,
            body_format=DeviceNetBodyFormat.DEVICENET_8_8,
            group_select=DeviceNetMessageGroup.MESSAGE_GROUP_3,
            source_message_id=0x9,
        )
        bus.shutdown()
    sys.exit(1)
    while 1:
        msg = dn.recv()
        if msg is None:
            break


if __name__ == "__main__":
    main()
