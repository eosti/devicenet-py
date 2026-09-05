import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Self

import bitstring
from bitstring import Bits

from devicenet.enums import DeviceNetFragmentationType

logger = logging.getLogger(__name__)

bitstring.options.lsb0 = True


@dataclass
class MessageField(ABC):
    @abstractmethod
    def pack(self) -> bytes:
        """Packs the dataclass into one or more bytes."""

    @abstractmethod
    def unpack(self, data: bytes) -> Self:
        """Unpacks one or more bytes into the dataclass."""


@dataclass
class DeviceNetExplicitHeader(MessageField):
    """A DeviceNet explicit message header.

    This structure is defined in IEC 62026-3:2014, section 5.2.1.2.
    """

    mac_id: int
    frag: bool = False
    xid: bool = False

    @classmethod
    def unpack(cls, data: bytes) -> Self:
        if len(data) != 1:
            raise ValueError("Length of header should be one byte.")
        header_bits = Bits(data)

        return cls(frag=header_bits[7], xid=header_bits[6], mac_id=header_bits[:6].uint)

    def pack(self) -> bytes:
        return bytes(Bits(bool=self.frag) + Bits(bool=self.xid) + Bits(uint=self.mac_id, length=6))


@dataclass
class DeviceNetServiceField(MessageField):
    """A DeviceNet explicit message service field.

    This structure is defined in IEC 62026-3:2014, section 5.2.1.3.
    """

    service_code: int
    is_response: bool = False  # Referred to as R/R bit in the spec

    @classmethod
    def unpack(cls, data: bytes) -> Self:
        if len(data) != 1:
            raise ValueError("Length of service field should be one byte.")
        if not isinstance(data, bytes):
            raise TypeError("Data needs to be in the form of bytes")

        field_bits = Bits(data)

        return cls(is_response=field_bits[7], service_code=field_bits[0:7].uint)

    def pack(self) -> bytes:
        return bytes(Bits(bool=self.is_response) + Bits(uint=self.service_code, length=7))


@dataclass
class DeviceNetFragmentProtocol(MessageField):
    """A DeviceNet fragmentation protocol field.

    This structure is defined in IEC 62026-3:2014, section 5.2.3.2.
    """

    fragment_type: DeviceNetFragmentationType
    fragmentation_count: int

    @classmethod
    def unpack(cls, data: bytes) -> Self:
        if len(data) != 1:
            raise ValueError("Length of fragmentation protocol should be one byte")

        if not isinstance(data, bytes):
            raise TypeError("Data needs to be in the form of bytes")

        field_bits = Bits(data)
        return cls(
            fragment_type=DeviceNetFragmentationType(field_bits[6:8].uint),
            fragmentation_count=field_bits[0:6].uint,
        )

    def pack(self) -> bytes:
        return bytes(
            Bits(uint=self.fragment_type, length=2) + Bits(uint=self.fragmentation_count, length=6)
        )


@dataclass
class DeviceNetAllocationChoiceByte(MessageField):
    """A DeviceNet allocation choice byte.

    Used in allocating master/slave connections.
    This structure is defined in IEC 62026-3:2014, section 5.5.3.1.2.

    While multicast_polled is changeable here, the spec says to leave this unset.
    """

    acknowledge_suppression: bool = False
    cyclic: bool = False
    change_of_state: bool = False
    bit_strobed: bool = False
    polled: bool = False
    explicit_message: bool = False
    multicast_polled: bool = False

    @classmethod
    def unpack(cls, data: bytes) -> Self:
        if len(data) != 1:
            raise ValueError("Length of fragmentation protocol should be one byte")

        if not isinstance(data, bytes):
            raise TypeError("Data needs to be in the form of bytes")

        field_bits = Bits(data)
        return cls(
            acknowledge_suppression=bool(field_bits[6]),
            cyclic=bool(field_bits[5]),
            change_of_state=bool(field_bits[4]),
            multicast_polled=bool(field_bits[3]),
            bit_strobed=bool(field_bits[2]),
            polled=bool(field_bits[1]),
            explicit_message=bool(field_bits[0]),
        )

    def pack(self) -> bytes:
        return bytes(
            Bits(bool=False)
            + Bits(bool=self.acknowledge_suppression)
            + Bits(bool=self.cyclic)
            + Bits(bool=self.change_of_state)
            + Bits(bool=self.multicast_polled)
            + Bits(bool=self.bit_strobed)
            + Bits(bool=self.polled)
            + Bits(bool=self.explicit_message)
        )
