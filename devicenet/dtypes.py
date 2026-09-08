import numbers
import struct
from datetime import UTC, datetime, time, timedelta
from enum import Enum
from typing import Any, Self

import pandas as pd


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
                days = int.from_bytes(val, byteorder="big", signed=False)
                return pd.Timestamp(1970, 1, 1, tzinfo=UTC) + pd.Timedelta(days=days)
            case cls.TIME_OF_DAY:
                cls.assert_length(val, 4)
                time_ms = int.from_bytes(val, byteorder="little", signed=False)
                delta = timedelta(milliseconds=time_ms)
                dt = datetime(1970, 1, 1, tzinfo=UTC) + delta
                return dt.time()
            case cls.REAL:
                cls.assert_length(val, 4)
                return struct.unpack("<f", val)[0]
            case cls.LREAL:
                cls.assert_length(val, 8)
                return struct.unpack("<d", val)[0]
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
                time_ms = int.from_bytes(val, byteorder="little", signed=True)
                return pd.Timedelta(milliseconds=time_ms)
            case cls.STIME:
                cls.assert_length(val, 8)
                time_ns = int.from_bytes(val, byteorder="little", signed=False)
                return pd.Timestamp(1970, 1, 1, tzinfo=UTC) + pd.Timedelta(nanoseconds=time_ns)
            case cls.UTIME:
                cls.assert_length(val, 8)
                time_us = int.from_bytes(val, byteorder="little", signed=False)
                return pd.Timestamp(1970, 1, 1, tzinfo=UTC) + pd.Timedelta(microseconds=time_us)
            case cls.ITIME:
                cls.assert_length(val, 2)
                time_ms = int.from_bytes(val, byteorder="little", signed=True)
                return pd.Timedelta(milliseconds=time_ms)
            case cls.FTIME:
                cls.assert_length(val, 4)
                time_us = int.from_bytes(val, byteorder="little", signed=True)
                return pd.Timedelta(microseconds=time_us)
            case cls.LTIME:
                cls.assert_length(val, 8)
                time_us = int.from_bytes(val, byteorder="little", signed=True)
                return pd.Timedelta(microseconds=time_us)
            case cls.NTIME:
                cls.assert_length(val, 8)
                time_ns = int.from_bytes(val, byteorder="little", signed=True)
                return pd.Timedelta(nanoseconds=time_ns)
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
                return val[2:].decode(encoding="utf-16-le")
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
                cls.assert_type(val, datetime)
                day_delta = (val - pd.Timestamp(1970, 1, 1, tzinfo=UTC)).days
                return day_delta.to_bytes(2, byteorder="big", signed=False)
            case cls.TIME_OF_DAY:
                cls.assert_type(val, time)
                ms = int(
                    val.hour * 3600000
                    + val.minute * 60000
                    + val.second * 1000
                    + val.microsecond / 1000
                )
                return ms.to_bytes(4, byteorder="little", signed=False)
            case cls.REAL:
                cls.assert_type(val, numbers.Real)
                return struct.pack("<f", val)
            case cls.LREAL:
                cls.assert_type(val, numbers.Real)
                return struct.pack("<d", val)
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
                cls.assert_type(val, timedelta)
                time_ms = int(val / pd.Timedelta(milliseconds=1))
                return time_ms.to_bytes(4, byteorder="little", signed=True)
            case cls.STIME:
                cls.assert_type(val, datetime)
                delta_time = val - pd.Timestamp(1970, 1, 1, tzinfo=UTC)
                time_ns = delta_time.value
                return time_ns.to_bytes(8, byteorder="little", signed=True)
            case cls.UTIME:
                cls.assert_type(val, datetime)
                delta_time = val - pd.Timestamp(1970, 1, 1, tzinfo=UTC)
                time_us = int(delta_time.value / 1e3)
                return time_us.to_bytes(8, byteorder="little", signed=True)
            case cls.ITIME:
                cls.assert_type(val, timedelta)
                time_ms = int(val / timedelta(milliseconds=1))
                return time_ms.to_bytes(2, byteorder="little", signed=True)
            case cls.FTIME:
                cls.assert_type(val, timedelta)
                time_us = int(val / pd.Timedelta(microseconds=1))
                return time_us.to_bytes(4, byteorder="little", signed=True)
            case cls.LTIME:
                cls.assert_type(val, timedelta)
                time_us = int(val / pd.Timedelta(microseconds=1))
                return time_us.to_bytes(8, byteorder="little", signed=True)
            case cls.NTIME:
                cls.assert_type(val, timedelta)
                time_ns = int(val / pd.Timedelta(nanoseconds=1))
                return time_ns.to_bytes(8, byteorder="little", signed=True)
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
                return b"".join([b.to_bytes(1, signed=False) for b in val])
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
                    encoding="utf-16-le"
                )
            case cls.STRINGN:
                raise NotImplementedError
            case cls.STRINGI:
                raise NotImplementedError
            case _:
                raise TypeError("Invalid DeviceNet datatype")
