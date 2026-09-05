import struct
from enum import Enum
from typing import Any, Self


class DeviceNetDatatype(Enum):
    """IEC 61158-5-2:2014 section 5.3."""

    NONE = 0
    BOOL = 1
    SWORD = 22
    WORD = 23
    DWORD = 24
    LWORD = 57
    DATE = 1001
    TIME_OF_DAY = 52
    REAL = 8
    LREAL = 15
    SINT = 2
    INT = 3
    DINT = 4
    LINT = 55
    USINT = 5
    UINT = 6
    UDINT = 7
    ULINT = 56
    TIME = 1002
    STIME = 1003
    UTIME = 1004
    ITIME = 1005
    FTIME = 1006
    LTIME = 1007
    NTIME = 1008
    BITSTRING = 14
    OCTETSTRING = 10
    EPATH = 1009
    ETH_MAC_ADDR = 1010
    DATE_AND_TIME = 1011
    SHORT_STRING = 1012
    STRING = 1013
    STRING2 = 1014
    STRINGN = 1015
    STRINGI = 1016
    STRINGI_ELEMENT = 1017
    STRUCT_UINT = 1018

    @staticmethod
    def assert_length(val: bytes, length: int) -> None:
        if len(val) != length:
            raise TypeError(
                f"Value has invalid length for dtype (got {len(val)}, expected {length})"
            )

    @staticmethod
    def assert_type(val: Any, dtype) -> None:
        if not isinstance(val, dtype):
            raise TypeError(f"Value has invalid type for dtype (got {type(val)}, expected {dtype})")

    @classmethod
    def decode(cls, val: bytes, dtype: Self) -> Any:
        match dtype:
            case cls.NONE:
                return val
            case cls.BOOL:
                cls.assert_length(val, 1)
                return bool(val[0])
            case cls.SWORD:
                cls.assert_length(val, 1)
                return val
            case cls.WORD:
                cls.assert_length(val, 2)
                return val
            case cls.DWORD:
                cls.assert_length(val, 4)
                return val
            case cls.LWORD:
                cls.assert_length(val, 8)
                return val
            case cls.DATE:
                cls.assert_length(val, 2)
                return int.from_bytes(val, byteorder="big", signed=False)
            case cls.TIME_OF_DAY:
                cls.assert_length(val, 4)
                return int.from_bytes(val, byteorder="big", signed=False)
            case cls.REAL:
                cls.assert_length(val, 4)
                return struct.unpack("<f", val)
            case cls.LREAL:
                cls.assert_length(val, 8)
                return struct.unpack("<ff", val)
            case cls.SINT:
                cls.assert_length(val, 1)
                return int.from_bytes(val, byteorder="little", signed=True)
            case cls.INT:
                cls.assert_length(val, 2)
                return int.from_bytes(val, byteorder="little", signed=True)
            case cls.DINT:
                cls.assert_length(val, 4)
                return int.from_bytes(val, byteorder="little", signed=True)
            case cls.LINT:
                cls.assert_length(val, 8)
                return int.from_bytes(val, byteorder="little", signed=True)
            case cls.USINT:
                cls.assert_length(val, 1)
                return int.from_bytes(val, byteorder="little", signed=False)
            case cls.UINT:
                cls.assert_length(val, 2)
                return int.from_bytes(val, byteorder="little", signed=False)
            case cls.UDINT:
                cls.assert_length(val, 4)
                return int.from_bytes(val, byteorder="little", signed=False)
            case cls.ULINT:
                cls.assert_length(val, 8)
                return int.from_bytes(val, byteorder="little", signed=False)
            case cls.TIME:
                cls.assert_length(val, 4)
                return int.from_bytes(val, byteorder="little", signed=True)
            case cls.STIME:
                cls.assert_length(val, 8)
                return int.from_bytes(val, byteorder="little", signed=False)
            case cls.UTIME:
                cls.assert_length(val, 8)
                return int.from_bytes(val, byteorder="little", signed=False)
            case cls.ITIME:
                cls.assert_length(val, 2)
                return int.from_bytes(val, byteorder="little", signed=True)
            case cls.FTIME:
                cls.assert_length(val, 4)
                return int.from_bytes(val, byteorder="little", signed=True)
            case cls.LTIME:
                cls.assert_length(val, 8)
                return int.from_bytes(val, byteorder="little", signed=True)
            case cls.NTIME:
                cls.assert_length(val, 8)
                return int.from_bytes(val, byteorder="little", signed=True)
            case cls.NTIME:
                cls.assert_length(val, 8)
                return int.from_bytes(val, byteorder="little", signed=True)
            case cls.BITSTRING:
                return val
            case cls.OCTETSTRING:
                return val
            case cls.EPATH:
                raise NotImplementedError
            case cls.ETH_MAC_ADDR:
                cls.assert_length(val, 6)
                return [int(b) for b in val]
            case cls.DATE_AND_TIME:
                raise NotImplementedError
            case cls.SHORT_STRING:
                count = cls.decode(val[0:1], cls.USINT)
                cls.assert_length(val, count + 1)
                return val[1:].decode(encoding="latin-1")
            case cls.STRING:
                count = cls.decode(val[0:2], cls.UINT)
                cls.assert_length(val, count + 2)
                return val[2:].decode(encoding="latin-1")
            case cls.STRING2:
                count = cls.decode(val[0:2], cls.UINT)
                cls.assert_length(val, count * 2 + 2)
                return val[2:].decode(encoding="utf-16")
            case cls.STRINGN:
                raise NotImplementedError
            case cls.STRINGI:
                raise NotImplementedError
            case _:
                raise TypeError("Invalid DeviceNet datatype")

    @classmethod
    def encode(cls, val: Any, dtype: Self) -> bytes:
        match dtype:
            case cls.NONE:
                raise TypeError("Can't encode None type")
            case cls.BOOL:
                cls.assert_type(val, bool)
                return bytes([val])
            case cls.SWORD:
                cls.assert_type(val, bytes)
                cls.assert_length(val, 1)
                return val
            case cls.WORD:
                cls.assert_type(val, bytes)
                cls.assert_length(val, 2)
                return val
            case cls.DWORD:
                cls.assert_type(val, bytes)
                cls.assert_length(val, 4)
                return val
            case cls.LWORD:
                cls.assert_type(val, bytes)
                cls.assert_length(val, 8)
                return val
            case cls.DATE:
                cls.assert_type(val, int)
                return val.to_bytes(2, byteorder="big", signed=False)
            case cls.TIME_OF_DAY:
                cls.assert_type(val, int)
                return val.to_bytes(4, byteorder="big", signed=False)
            case cls.REAL:
                cls.assert_type(val, float)
                return struct.pack("<f", val)
            case cls.LREAL:
                cls.assert_type(val, float)
                return struct.pack("<ff", val)
            case cls.SINT:
                cls.assert_type(val, int)
                return val.to_bytes(1, byteorder="little", signed=True)
            case cls.INT:
                cls.assert_type(val, int)
                return val.to_bytes(2, byteorder="little", signed=True)
            case cls.DINT:
                cls.assert_type(val, int)
                return val.to_bytes(4, byteorder="little", signed=True)
            case cls.LINT:
                cls.assert_type(val, int)
                return val.to_bytes(8, byteorder="little", signed=True)
            case cls.USINT:
                cls.assert_type(val, int)
                return val.to_bytes(1, byteorder="little", signed=False)
            case cls.UINT:
                cls.assert_type(val, int)
                return val.to_bytes(2, byteorder="little", signed=False)
            case cls.UDINT:
                cls.assert_type(val, int)
                return val.to_bytes(4, byteorder="little", signed=False)
            case cls.ULINT:
                cls.assert_type(val, int)
                return val.to_bytes(8, byteorder="little", signed=False)
            case cls.TIME:
                cls.assert_type(val, int)
                return val.to_bytes(4, byteorder="little", signed=True)
            case cls.STIME:
                cls.assert_type(val, int)
                return val.to_bytes(8, byteorder="little", signed=True)
            case cls.UTIME:
                cls.assert_type(val, int)
                return val.to_bytes(8, byteorder="little", signed=False)
            case cls.ITIME:
                cls.assert_type(val, int)
                return val.to_bytes(2, byteorder="little", signed=True)
            case cls.FTIME:
                cls.assert_type(val, int)
                return val.to_bytes(4, byteorder="little", signed=True)
            case cls.LTIME:
                cls.assert_type(val, int)
                return val.to_bytes(8, byteorder="little", signed=True)
            case cls.NTIME:
                cls.assert_type(val, int)
                return val.to_bytes(8, byteorder="little", signed=True)
            case cls.BITSTRING:
                cls.assert_type(val, bytes)
                return val
            case cls.OCTETSTRING:
                cls.assert_type(val, bytes)
                return val
            case cls.EPATH:
                raise NotImplementedError
            case cls.ETH_MAC_ADDR:
                cls.assert_type(val, list)
                cls.assert_length(val, 6)
                return bytes([val.to_bytes(1, signed=False) for b in val])
            case cls.DATE_AND_TIME:
                raise NotImplementedError
            case cls.SHORT_STRING:
                cls.assert_type(val, str)
                count = len(val)
                return count.to_bytes(1, signed=False) + val.encode(encoding="latin-1")
            case cls.STRING:
                cls.assert_type(val, str)
                count = len(val)
                return count.to_bytes(2, byteorder="little", signed=False) + val.encode(
                    encoding="latin-1"
                )
            case cls.STRING2:
                cls.assert_type(val, str)
                count = len(val)
                return count.to_bytes(2, byteorder="little", signed=False) + val.encode(
                    encoding="utf-16"
                )
            case cls.STRINGN:
                raise NotImplementedError
            case cls.STRINGI:
                raise NotImplementedError
            case _:
                raise TypeError("Invalid DeviceNet datatype")
