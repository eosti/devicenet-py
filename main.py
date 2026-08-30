import logging
import sys

from can.interface import Bus

from devicenet.devicenet import DeviceNet
from devicenet.enums import DeviceNetBodyFormat, DeviceNetMessageGroup


def main():
    logging.basicConfig(level=logging.DEBUG)

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
    while 1:
        dn.handle_messages()
    sys.exit(1)
    while 1:
        msg = dn.recv()
        if msg is None:
            break


if __name__ == "__main__":
    main()
