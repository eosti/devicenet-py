import logging
from dataclasses import dataclass

import bitstring
from bitstring import Bits

from devicenet.enums import (
    DeviceNetMessageGroup,
)

logger = logging.getLogger(__name__)

bitstring.options.lsb0 = True


@dataclass
class DeviceNetCID:
    message_group: DeviceNetMessageGroup
    message_id: int | None = None
    mac_id: int | None = None

    @classmethod
    def unpack(cls, cid: int):
        """Unpacks a CID into the dataclass."""
        cid_bits = Bits(uint=cid, length=11)
        if cid_bits[10:] == "0b0":
            return cls(
                DeviceNetMessageGroup.MESSAGE_GROUP_1,
                message_id=cid_bits[6:10].uint,
                mac_id=cid_bits[0:6].uint,
            )
        if cid_bits[9:] == "0b10":
            return cls(
                DeviceNetMessageGroup.MESSAGE_GROUP_2,
                message_id=cid_bits[0:3].uint,
                mac_id=cid_bits[3:9].uint,
            )
        if cid_bits[9:] == "0b11" and cid_bits[6:9] != "0b111":
            return cls(
                DeviceNetMessageGroup.MESSAGE_GROUP_3,
                message_id=cid_bits[6:9].uint,
                mac_id=cid_bits[0:6].uint,
            )
        if cid_bits[6:] == "0b11111" and cid_bits[4:6] != "0b11":
            return cls(
                DeviceNetMessageGroup.MESSAGE_GROUP_4, message_id=cid_bits[0:6].uint
            )

        raise ValueError(f"Invalid CID 0x{cid:04X}")

    def pack(self) -> int:
        """Packs the dataclass into a valid CID."""
        if self.message_group == DeviceNetMessageGroup.MESSAGE_GROUP_1:
            return (
                Bits("0b0")
                + Bits(uint=self.message_id, length=4)
                + Bits(uint=self.mac_id, length=6)
            ).uint
        if self.message_group == DeviceNetMessageGroup.MESSAGE_GROUP_2:
            return (
                Bits("0b10")
                + Bits(uint=self.mac_id, length=6)
                + Bits(uint=self.message_id, length=3)
            ).uint
        if self.message_group == DeviceNetMessageGroup.MESSAGE_GROUP_3:
            return (
                Bits("0b11")
                + Bits(uint=self.message_id, length=3)
                + Bits(uint=self.mac_id, length=6)
            ).uint
        if self.message_group == DeviceNetMessageGroup.MESSAGE_GROUP_4:
            return (Bits("0b11111") + Bits(uint=self.message_id, length=6)).uint
