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
    DeviceNetAllocationChoiceByte,
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
    def unpack(self, data: bytes | list[bytes]) -> Self:
        """Unpacks a message into the dataclass."""


@dataclass
class DeviceNetEmptyMessage(DeviceNetMessage):
    def pack(self):
        yield None

    @classmethod
    def unpack(cls, data) -> Self:
        if len(data) != 0:
            raise ValueError("Data passed to empty message")
        return cls()


@dataclass
class DeviceNetDataMessage(DeviceNetMessage):
    data: bytes

    def pack(self):
        for i in range(0, len(self.data), 8):
            if i == len(self.data) - len(self.data) % 8:
                yield self.data[i:]
                return
            else:
                yield self.data[i : i + 8]

    @classmethod
    def unpack(cls, data: bytes | list[bytes]) -> Self:
        if not isinstance(data, bytes):
            data = b"".join(data)
        return cls(data)


@dataclass
class DeviceNetExplicitMessage(DeviceNetMessage):
    mac_id: int
    message: bytes | None
    xid: bool = False

    def pack(self) -> Iterator[bytes]:
        if len(self.body) <= 7:
            header = DeviceNetExplicitHeader(mac_id=self.mac_id, xid=self.xid)
            yield header.pack() + self.body
            return

        header = DeviceNetExplicitHeader(mac_id=self.mac_id, frag=True, xid=self.xid)
        for i in range(0, len(self.body), 6):
            if i == 0:
                data_chunk = self.body[i : i + 6]
                fragment_byte = DeviceNetFragmentProtocol(
                    DeviceNetFragmentationType.FIRST_FRAGMENT, 0
                )
            elif i == len(self.body) - len(self.body) % 6:
                data_chunk = self.body[i:]
                fragment_byte = DeviceNetFragmentProtocol(
                    DeviceNetFragmentationType.LAST_FRAGMENT, int(i / 6)
                )
            else:
                data_chunk = self.body[i : i + 6]
                fragment_byte = DeviceNetFragmentProtocol(
                    DeviceNetFragmentationType.MIDDLE_FRAGMENT, int(i / 6)
                )

            yield header.pack() + fragment_byte.pack() + data_chunk

    @property
    def body(self) -> bytes:
        if not isinstance(self.message, bytes):
            raise TypeError("Message must be a bytes object")

        if self.message is None:
            return b""

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
                    raise RuntimeError("First fragment found after other fragments processed")

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
        if self.message is None:
            return service_field.pack()
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
class DeviceNetExplicitRequestMessage(DeviceNetExplicitMessageGenericService):
    """A devicenet explicit request message for message body format values 0-3.

    Service data goes in self.message.

    This structure is defined in IEC 62026-3:2014, section 5.2.1.6.2.
    """

    class_id: int = 0x00
    instance_id: int = 0x00
    body_format: DeviceNetBodyFormat = DeviceNetBodyFormat.DEVICENET_8_8

    @property
    def body(self) -> bytes:
        if not isinstance(self.message, bytes):
            raise TypeError("Message must be a bytes object")

        service_field = DeviceNetServiceField(
            service_code=self.service_code, is_response=self.is_response
        )
        if self.body_format == DeviceNetBodyFormat.DEVICENET_8_8:
            class_field = Bits(uint=self.class_id, length=8)
            instance_field = Bits(uint=self.instance_id, length=8)
        elif self.body_format == DeviceNetBodyFormat.DEVICENET_8_16:
            # TODO: endianness?
            class_field = Bits(uint=self.class_id, length=8)
            instance_field = Bits(uint=self.instance_id, length=16)
        elif self.body_format == DeviceNetBodyFormat.DEVICENET_16_8:
            class_field = Bits(uint=self.class_id, length=16)
            instance_field = Bits(uint=self.instance_id, length=8)
        elif self.body_format == DeviceNetBodyFormat.DEVICENET_16_16:
            class_field = Bits(uint=self.class_id, length=16)
            instance_field = Bits(uint=self.instance_id, length=16)
        else:
            raise ValueError("CIP paths not implemented here")

        if self.message is None:
            return service_field.pack() + class_field.bytes + instance_field.bytes

        return service_field.pack() + class_field.bytes + instance_field.bytes + self.message

    @classmethod
    def unpack(cls, data):
        if not isinstance(data, bytes):
            data = cls.unfragment(data)
            raise NotImplementedError

        # TODO: how to get/determine body format
        body_format = 0

        header = DeviceNetExplicitHeader.unpack(data[0:1])
        service_field = DeviceNetServiceField.unpack(data[1:2])

        if body_format == DeviceNetBodyFormat.DEVICENET_8_8:
            class_field = Bits(data[2:3])
            instance_field = Bits(data[3:4])
            service_data = data[4:]
        elif body_format == DeviceNetBodyFormat.DEVICENET_8_16:
            class_field = Bits(data[2:3])
            instance_field = Bits(data[3:5])
            service_data = data[5:]
        elif body_format == DeviceNetBodyFormat.DEVICENET_16_8:
            class_field = Bits(data[2:4])
            instance_field = Bits(data[4:5])
            service_data = data[5:]
        elif body_format == DeviceNetBodyFormat.DEVICENET_16_16:
            class_field = Bits(data[2:4])
            instance_field = Bits(data[4:6])
            service_data = data[6:]
        else:
            raise ValueError("CIP paths not implemented here")

        return cls(
            mac_id=header.mac_id,
            xid=header.xid,
            service_code=service_field.service_code,
            is_response=service_field.is_response,
            class_id=class_field.uint,
            instance_id=instance_field.uint,
            message=service_data,
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
        byte_four_five = self.connection_instance_id.to_bytes(2, "little", signed=False)
        yield (
            header.pack()
            + service_field.pack()
            + byte_two.bytes
            + byte_three.bytes
            + byte_four_five
        )

    @classmethod
    def unpack(cls, data: bytes | list[bytes]) -> Self:
        if not isinstance(data, bytes):
            raise TypeError("Data should be a single bytes object")
        header = DeviceNetExplicitHeader.unpack(data[0:1])
        service_field = DeviceNetServiceField.unpack(data[1:2])
        byte_two = Bits(uint=data[2], length=8)
        byte_three = Bits(uint=data[3], length=8)
        connection_instance = int.from_bytes(data[4:6], "little", signed=False)
        if service_field.service_code != 0x4B:
            raise RuntimeError("Invalid service code for this message")

        if not service_field.is_response:
            raise RuntimeError("Message is request, expecting response")

        return cls(
            dest_mac=header.mac_id,
            body_format=DeviceNetBodyFormat(byte_two[0:4].uint),
            destination_message_id=byte_three[4:8].uint,
            source_message_id=byte_three[0:4].uint,
            connection_instance_id=connection_instance,
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
        header = Bits(bool=self.is_response) + Bits(uint=self.physical_port_number, length=7)
        vendor_id = self.vendor_id.to_bytes(2, "little", signed=False)
        serial_number = self.serial_number.to_bytes(4, "little", signed=False)
        yield header.bytes + vendor_id + serial_number

    @classmethod
    def unpack(cls, data: bytes | list[bytes]) -> Self:
        if not isinstance(data, bytes):
            raise TypeError("Data should be a single bytes object")
        header = Bits(uint=data[0], length=8)
        vendor_id = int.from_bytes(data[1:3], byteorder="little", signed=False)
        serial_number = int.from_bytes(data[3:7], byteorder="little", signed=False)

        return cls(
            is_response=header[7],
            physical_port_number=header[0:7].uint,
            vendor_id=vendor_id,
            serial_number=serial_number,
        )


@dataclass
class DeviceNetAllocateMasterSlaveConnectionRequestMessage(DeviceNetMessage):
    mac_id: int
    allocation_choice: DeviceNetAllocationChoiceByte
    allocator_id: int

    def pack(self) -> Iterator[bytes]:
        header = DeviceNetExplicitHeader(mac_id=self.mac_id)
        service = DeviceNetServiceField(service_code=0x4B)
        final_byte = Bits(uint=self.allocator_id, length=6)

        yield (
            header.pack()
            + service.pack()
            + bytes([0x03, 0x01])
            + self.allocation_choice.pack()
            + final_byte.tobytes()
        )

    @classmethod
    def unpack(cls, data):
        if not isinstance(data, bytes):
            raise TypeError("Data should be a single bytes object")
        if len(data) != 6:
            raise ValueError("Expected 6 bytes in the message")

        header = DeviceNetExplicitHeader.unpack(data[0:1])
        service = DeviceNetServiceField.unpack(data[1:2])

        if service.service_code != 0x4B:
            raise ValueError("Message is does not have correct service code")

        allocation_choice = DeviceNetAllocationChoiceByte.unpack(data[4:5])
        allocator_id = Bits(data[6:7])[0:6]

        return cls(
            mac_id=header.mac_id,
            allocation_choice=allocation_choice,
            allocator_id=allocator_id.uint,
        )


@dataclass
class DeviceNetAllocateMasterSlaveConnectionResponseMessage(DeviceNetMessage):
    mac_id: int
    message_body_format: DeviceNetBodyFormat

    def pack(self):
        header = DeviceNetExplicitHeader(mac_id=self.mac_id)
        service = DeviceNetServiceField(service_code=0x4B, is_response=True)
        second_byte = Bits(uint=0, length=4) + Bits(uint=self.message_body_format, length=4)

        yield header.pack() + service.pack() + second_byte.bytes

    @classmethod
    def unpack(cls, data):
        if not isinstance(data, bytes):
            raise TypeError("Data should be a single bytes object")
        if len(data) != 3:
            raise ValueError("Expected 3 bytes in the message")

        header = DeviceNetExplicitHeader.unpack(data[0:1])
        service = DeviceNetServiceField.unpack(data[1:2])

        if service.service_code != 0x4B:
            logger.debug(service)
            raise ValueError("Message is does not have correct service code")

        message_body_format = DeviceNetBodyFormat(Bits(data[2:3])[0:3].uint)

        return cls(mac_id=header.mac_id, message_body_format=message_body_format)
