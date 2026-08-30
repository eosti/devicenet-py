import logging
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Self

import bitstring
from bitstring import Bits

from devicenet.enums import (
    DeviceNetBodyFormat,
    DeviceNetFragmentationType,
    DeviceNetMessageGroup,
)
from devicenet.fields import (
    DeviceNetExplicitHeader,
    DeviceNetFragmentProtocol,
    DeviceNetServiceField,
)

logger = logging.getLogger(__name__)

bitstring.options.lsb0 = True


@dataclass
class DeviceNetMessage(ABC):
    @abstractmethod
    def pack(self) -> Iterator[bytes]:
        """Packs the message into an Iterable of 8 bytes or less."""

    @abstractmethod
    def unpack(cls, data: bytes | list[bytes]) -> Self:
        """Unpacks a message into the dataclass."""


@dataclass
class DeviceNetExplicitMessage(DeviceNetMessage):
    mac_id: int
    message: bytes
    xid: bool = False

    def pack(self) -> Iterator[bytes]:
        if len(self.body) <= 7:
            header = DeviceNetExplicitHeader(mac_id=self.mac_id, xid=self.xid)
            yield header.pack() + self.body
            return

        header = DeviceNetExplicitHeader(mac_id=self.mac_id, frag=True, xid=self.xid)
        int((len(self.body) - 1) / 6) + 1
        for i in range(0, len(self.body), 6):
            data_chunk = self.body[i : i + 6]
            if i == 0:
                fragment_byte = DeviceNetFragmentProtocol(
                    DeviceNetFragmentationType.FIRST_FRAGMENT, 0
                )
            elif i == len(self.body) - len(self.body) % 6:
                fragment_byte = DeviceNetFragmentProtocol(
                    DeviceNetFragmentationType.LAST_FRAGMENT, int(i / 6)
                )
            else:
                fragment_byte = DeviceNetFragmentProtocol(
                    DeviceNetFragmentationType.MIDDLE_FRAGMENT, int(i / 6)
                )

            yield header.pack() + fragment_byte.pack() + data_chunk

    @property
    def body(self) -> bytes:
        if not isinstance(self.message, bytes):
            raise TypeError("Message must be a bytes object")

        return self.message

    @staticmethod
    def unfragment(frames: list[bytes]) -> bytes:
        frame_count = 0
        all_data = bytearray()
        for f in frames:
            header = DeviceNetExplicitHeader.unpack(f[0:1])
            if not header.frag:
                if frame_count == 0 and len(frames) == 1:
                    return f
                raise RuntimeError("Non-fragmented frame found during defragmentation")

            frag_proto = DeviceNetFragmentProtocol.unpack(f[1:2])
            if frag_proto.fragment_type == DeviceNetFragmentationType.FIRST_FRAGMENT:
                if frag_proto.fragmentation_count == 0x3F:
                    return f[0:1] + f[2:8]
                if frame_count != 0:
                    raise RuntimeError(
                        "First fragment found after other fragments processed"
                    )

                header.frag = False
                all_data += header.pack()

            if frag_proto.fragmentation_count != frame_count:
                logger.error(
                    "Processing fragment %s but got index %s",
                    frame_count,
                    frag_proto.fragmentation_count,
                )
                raise RuntimeError("Out-of-order fragments found")

            all_data += f[2:8]
            frame_count += 1

            if frag_proto.fragment_type == DeviceNetFragmentationType.LAST_FRAGMENT:
                logger.debug("defragmentation: processed %s fragments", frame_count)
                header.frag = False
                return bytes(all_data)

        logger.warning("No final fragment found, data may be incomplete")
        logger.debug("defragmentation: processed %s fragments", frame_count)
        return bytes(all_data)

    @classmethod
    def unpack(cls, data: bytes | list[bytes]) -> Self:
        if not isinstance(data, bytes):
            data = cls.unfragment(data)
        header = DeviceNetExplicitHeader.unpack(data[0:1])
        return cls(mac_id=header.mac_id, xid=header.xid, message=data[1:])


@dataclass
class DeviceNetExplicitMessageGenericService(DeviceNetExplicitMessage):
    """A DeviceNet explicit message with generic service.

    This structure is defined in IEC 62026-3:2014, section 5.2.1.3.
    """

    service_code: int = 0x00
    is_response: bool = False

    @property
    def body(self) -> bytes:
        if not isinstance(self.message, bytes):
            raise TypeError("Message must be a bytes object")

        service_field = DeviceNetServiceField(
            service_code=self.service_code, is_response=self.is_response
        )
        return service_field.pack() + self.message

    @classmethod
    def unpack(cls, data: bytes | list[bytes]) -> Self:
        if not isinstance(data, bytes):
            data = cls.unfragment(data)
        header = DeviceNetExplicitHeader.unpack(data[0:1])
        service_field = DeviceNetServiceField.unpack(data[1:2])
        return cls(
            mac_id=header.mac_id,
            xid=header.xid,
            service_code=service_field.service_code,
            is_response=service_field.is_response,
            message=data[2:],
        )


@dataclass
class DeviceNetExplicitMessagingConnectionRequestMessage(DeviceNetMessage):
    """A DeviceNet explicit messaging connection request message body.

    This structure is defined in IEC 62026-3:2014, section 5.2.1.5.2.
    """

    dest_mac: int
    body_format: DeviceNetBodyFormat
    group_select: DeviceNetMessageGroup
    source_message_id: int

    def pack(self) -> Iterator[bytes]:
        header = DeviceNetExplicitHeader(self.dest_mac)
        service_field = DeviceNetServiceField(0x4B)
        byte_two = Bits("0b0000") + Bits(uint=self.body_format, length=4)
        byte_three = Bits(uint=self.group_select, length=4) + Bits(
            uint=self.source_message_id, length=4
        )
        yield header.pack() + service_field.pack() + byte_two.bytes + byte_three.bytes

    @classmethod
    def unpack(cls, data: bytes | list[bytes]) -> Self:
        if not isinstance(data, bytes):
            raise TypeError("Data should be a single bytes object")
        header = DeviceNetExplicitHeader.unpack(data[0:1])
        service_field = DeviceNetServiceField.unpack(data[1:2])
        byte_two = Bits(uint=data[2], length=8)
        byte_three = Bits(uint=data[3], length=8)

        if service_field.service_code != 0x4B:
            raise RuntimeError("Invalid service code for this message")

        if service_field.is_response:
            raise RuntimeError("Message is response, expecting request")

        return cls(
            dest_mac=header.mac_id,
            body_format=DeviceNetBodyFormat(byte_two[0:4].uint),
            group_select=DeviceNetMessageGroup(byte_three[4:8].uint),
            source_message_id=byte_three[0:4].uint,
        )


@dataclass
class DeviceNetExplicitMessagingConnectionResponseMessage(DeviceNetMessage):
    """A DeviceNet explicit messaging connection request message body.

    This structure is defined in IEC 62026-3:2014, section 5.2.1.5.3.
    """

    dest_mac: int
    body_format: DeviceNetBodyFormat
    destination_message_id: int
    source_message_id: int
    connection_instance_id: int

    def pack(self) -> Iterator[bytes]:
        header = DeviceNetExplicitHeader(self.dest_mac)
        service_field = DeviceNetServiceField(0x4B, is_response=True)
        byte_two = Bits("0b0000") + Bits(uint=self.body_format, length=4)
        byte_three = Bits(uint=self.destination_message_id, length=4) + Bits(
            uint=self.source_message_id, length=4
        )
        byte_four_five = Bits(uint=self.connection_instance_id, length=16)
        yield (
            header.pack()
            + service_field.pack()
            + byte_two.bytes
            + byte_three.bytes
            + byte_four_five.bytes[::-1]
        )

    @classmethod
    def unpack(cls, data: bytes | list[bytes]) -> Self:
        if not isinstance(data, bytes):
            raise TypeError("Data should be a single bytes object")
        header = DeviceNetExplicitHeader.unpack(data[0:1])
        service_field = DeviceNetServiceField.unpack(data[1:2])
        byte_two = Bits(uint=data[2], length=8)
        byte_three = Bits(uint=data[3], length=8)
        connection_instance = Bits(uint=data[5], length=8) + Bits(
            uint=data[4], length=8
        )

        if service_field.service_code != 0x4B:
            raise RuntimeError("Invalid service code for this message")

        if not service_field.is_response:
            raise RuntimeError("Message is request, expecting response")

        return cls(
            dest_mac=header.mac_id,
            body_format=DeviceNetBodyFormat(byte_two[0:4].uint),
            destination_message_id=byte_three[4:8].uint,
            source_message_id=byte_three[0:4].uint,
            connection_instance_id=connection_instance.uint,
        )


@dataclass
class DeviceNetDuplicateMACIDCheckMessage(DeviceNetMessage):
    """A DeviceNet Duplicate MAC ID detection message.

    This structure is defined in IEC 62026-3:2014, section 5.2.7.
    """

    physical_port_number: int
    vendor_id: int
    serial_number: int
    is_response: bool = False

    def pack(self) -> Iterator[bytes]:
        header = Bits(bool=self.is_response) + Bits(
            uint=self.physical_port_number, length=7
        )
        vendor_id = Bits(uint=self.vendor_id, length=16)
        serial_number = Bits(uint=self.serial_number, length=32)
        # TODO: verify that these put the high byte last
        yield header.bytes + vendor_id.bytes[::-1] + serial_number.bytes[::-1]

    @classmethod
    def unpack(cls, data: bytes | list[bytes]) -> Self:
        if not isinstance(data, bytes):
            raise TypeError("Data should be a single bytes object")
        header = Bits(uint=data[0], length=8)
        vendor_id = Bits(data[1:3])
        serial_number = Bits(data[3:7])

        return cls(
            is_response=header[7],
            physical_port_number=header[0:7].uint,
            vendor_id=vendor_id.uint,
            serial_number=serial_number.uint,
        )
