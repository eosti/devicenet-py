import math
import random
from datetime import UTC, datetime, time, timedelta

import pandas as pd
import pytest

from devicenet.dtypes import DeviceNetDatatype


def test_dtype_none():
    data = random.randbytes(8)
    assert DeviceNetDatatype.decode(data, DeviceNetDatatype.NONE) == data

    with pytest.raises(TypeError):
        DeviceNetDatatype.encode(data, DeviceNetDatatype.NONE)


def test_dtype_bool():
    assert DeviceNetDatatype.decode(bytes([0x00]), DeviceNetDatatype.BOOL) == False  # noqa: E712
    assert DeviceNetDatatype.decode(bytes([0x01]), DeviceNetDatatype.BOOL) == True  # noqa: E712

    with pytest.raises(TypeError):
        DeviceNetDatatype.decode(bytes([0x01, 0x00]), DeviceNetDatatype.BOOL)

    assert DeviceNetDatatype.encode(True, DeviceNetDatatype.BOOL) == bytes([0x01])
    assert DeviceNetDatatype.encode(False, DeviceNetDatatype.BOOL) == bytes([0x00])

    with pytest.raises(TypeError):
        DeviceNetDatatype.encode(0, DeviceNetDatatype.BOOL)
    with pytest.raises(TypeError):
        DeviceNetDatatype.encode(1, DeviceNetDatatype.BOOL)


@pytest.mark.parametrize(
    ("dtype_name", "dtype_len"),
    [
        ("SWORD", 1),
        ("WORD", 2),
        ("DWORD", 4),
        ("LWORD", 8),
    ],
)
def test_dtype_word(dtype_name, dtype_len):
    data = random.randbytes(dtype_len)
    dtype = getattr(DeviceNetDatatype, dtype_name)

    assert DeviceNetDatatype.encode(data, dtype) == data
    assert DeviceNetDatatype.decode(data, dtype) == data

    with pytest.raises(TypeError):
        data_long = random.randbytes(dtype_len + 1)
        DeviceNetDatatype.encode(data_long, dtype)

    with pytest.raises(TypeError):
        data_long = random.randbytes(dtype_len + 1)
        DeviceNetDatatype.decode(data_long, dtype)


@pytest.mark.parametrize(
    ("decimal_rep", "byte_rep"),
    [
        (3.14, bytes([0xC3, 0xF5, 0x48, 0x40])),
        (0, bytes([0x00, 0x00, 0x00, 0x00])),
        (100, bytes([0x00, 0x00, 0xC8, 0x42])),
        (-100, bytes([0x00, 0x00, 0xC8, 0xC2])),
        (25.45, bytes([0x9A, 0x99, 0xCB, 0x41])),
        (float("nan"), bytes([0x00, 0x00, 0xC0, 0x7F])),
        (float("-inf"), bytes([0x00, 0x00, 0x80, 0xFF])),
        (float("+inf"), bytes([0x00, 0x00, 0x80, 0x7F])),
    ],
)
def test_dtype_real(decimal_rep, byte_rep):
    assert DeviceNetDatatype.encode(decimal_rep, DeviceNetDatatype.REAL) == byte_rep
    if math.isnan(decimal_rep):
        assert math.isnan(DeviceNetDatatype.decode(byte_rep, DeviceNetDatatype.REAL))
    else:
        assert DeviceNetDatatype.decode(byte_rep, DeviceNetDatatype.REAL) == pytest.approx(
            decimal_rep
        )


@pytest.mark.parametrize(
    ("decimal_rep", "byte_rep"),
    [
        (3.14, bytes.fromhex("1F85EB51B81E0940")),
        (0, bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])),
        (100, bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x59, 0x40])),
        (-100, bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x59, 0xC0])),
        (25.45, bytes.fromhex("3333333333733940")),
        (float("nan"), bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xF8, 0x7F])),
        (float("-inf"), bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xF0, 0xFF])),
        (float("+inf"), bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xF0, 0x7F])),
    ],
)
def test_dtype_lreal(decimal_rep, byte_rep):
    assert DeviceNetDatatype.encode(decimal_rep, DeviceNetDatatype.LREAL) == byte_rep
    if math.isnan(decimal_rep):
        assert math.isnan(DeviceNetDatatype.decode(byte_rep, DeviceNetDatatype.LREAL))
    else:
        assert DeviceNetDatatype.decode(byte_rep, DeviceNetDatatype.LREAL) == pytest.approx(
            decimal_rep
        )


@pytest.mark.parametrize(
    ("decimal_rep", "byte_rep"),
    [
        (127, bytes([0x7F])),
        (-127, bytes([0x81])),
    ],
)
def test_dtype_sint(decimal_rep, byte_rep):
    assert DeviceNetDatatype.encode(decimal_rep, DeviceNetDatatype.SINT) == byte_rep
    assert DeviceNetDatatype.decode(byte_rep, DeviceNetDatatype.SINT) == decimal_rep


@pytest.mark.parametrize(
    ("decimal_rep", "byte_rep"),
    [
        (42, bytes([0x2A])),
        (255, bytes([0xFF])),
    ],
)
def test_dtype_usint(decimal_rep, byte_rep):
    assert DeviceNetDatatype.encode(decimal_rep, DeviceNetDatatype.USINT) == byte_rep
    assert DeviceNetDatatype.decode(byte_rep, DeviceNetDatatype.USINT) == decimal_rep


@pytest.mark.parametrize(
    ("decimal_rep", "byte_rep"),
    [
        (42, bytes([0x2A, 0x00])),
        (255, bytes([0xFF, 0x00])),
        (54298, bytes([0x1A, 0xD4])),
        (65535, bytes([0xFF, 0xFF])),
    ],
)
def test_dtype_uint(decimal_rep, byte_rep):
    assert DeviceNetDatatype.encode(decimal_rep, DeviceNetDatatype.UINT) == byte_rep
    assert DeviceNetDatatype.decode(byte_rep, DeviceNetDatatype.UINT) == decimal_rep


@pytest.mark.parametrize(
    ("decimal_rep", "byte_rep"),
    [
        (42, bytes([0x2A, 0x00, 0x00, 0x00])),
        (255, bytes([0xFF, 0x00, 0x00, 0x00])),
        (54298, bytes([0x1A, 0xD4, 0x00, 0x00])),
        (65535, bytes([0xFF, 0xFF, 0x00, 0x00])),
        (4294967295, bytes([0xFF, 0xFF, 0xFF, 0xFF])),
    ],
)
def test_dtype_udint(decimal_rep, byte_rep):
    assert DeviceNetDatatype.encode(decimal_rep, DeviceNetDatatype.UDINT) == byte_rep
    assert DeviceNetDatatype.decode(byte_rep, DeviceNetDatatype.UDINT) == decimal_rep


@pytest.mark.parametrize(
    ("decimal_rep", "byte_rep"),
    [
        (42, bytes([0x2A, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])),
        (255, bytes([0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])),
        (54298, bytes([0x1A, 0xD4, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])),
        (65535, bytes([0xFF, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])),
        (4294967295, bytes([0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x00])),
    ],
)
def test_dtype_ulint(decimal_rep, byte_rep):
    assert DeviceNetDatatype.encode(decimal_rep, DeviceNetDatatype.ULINT) == byte_rep
    assert DeviceNetDatatype.decode(byte_rep, DeviceNetDatatype.ULINT) == decimal_rep


def test_dtype_stime():
    date_rep = datetime(2009, 2, 13, 23, 31, 30, tzinfo=UTC)
    byte_rep = bytes([0x00, 0xB4, 0x8D, 0x76, 0xF4, 0x10, 0x22, 0x11])

    assert DeviceNetDatatype.encode(date_rep, DeviceNetDatatype.STIME) == byte_rep
    assert DeviceNetDatatype.decode(byte_rep, DeviceNetDatatype.STIME) == date_rep


def test_dtype_utime():
    date_rep = datetime(2009, 2, 13, 23, 31, 30, tzinfo=UTC)
    byte_rep = bytes([0x80, 0xD8, 0x88, 0x3C, 0xD5, 0x62, 0x04, 0x00])

    assert DeviceNetDatatype.encode(date_rep, DeviceNetDatatype.UTIME) == byte_rep
    assert DeviceNetDatatype.decode(byte_rep, DeviceNetDatatype.UTIME) == date_rep


def test_dtype_date():
    date_rep = datetime(2009, 2, 13, tzinfo=UTC)
    byte_rep = bytes([0x37, 0xD0])

    assert DeviceNetDatatype.encode(date_rep, DeviceNetDatatype.DATE) == byte_rep
    assert DeviceNetDatatype.decode(byte_rep, DeviceNetDatatype.DATE) == date_rep


def test_dtype_time_of_date():
    time_rep = time(hour=7, minute=47, second=7)
    byte_rep = bytes([0x78, 0xA8, 0xAB, 0x01])

    assert DeviceNetDatatype.encode(time_rep, DeviceNetDatatype.TIME_OF_DAY) == byte_rep
    assert DeviceNetDatatype.decode(byte_rep, DeviceNetDatatype.TIME_OF_DAY) == time_rep


@pytest.mark.parametrize(
    ("decimal_rep", "byte_rep"),
    [
        (127, bytes([0x7F, 0x00])),
        (-127, bytes([0x81, 0xFF])),
        (32767, bytes([0xFF, 0x7F])),
        (-32768, bytes([0x00, 0x80])),
    ],
)
class TestTwoByteSigned:
    @staticmethod
    def test_dtype_int(decimal_rep, byte_rep):
        assert DeviceNetDatatype.encode(decimal_rep, DeviceNetDatatype.INT) == byte_rep
        assert DeviceNetDatatype.decode(byte_rep, DeviceNetDatatype.INT) == decimal_rep

    @staticmethod
    def test_itime_int(decimal_rep, byte_rep):
        time_rep = timedelta(milliseconds=decimal_rep)
        assert DeviceNetDatatype.encode(time_rep, DeviceNetDatatype.ITIME) == byte_rep
        assert DeviceNetDatatype.decode(byte_rep, DeviceNetDatatype.ITIME) == time_rep


@pytest.mark.parametrize(
    ("decimal_rep", "byte_rep"),
    [
        (127, bytes([0x7F, 0x00, 0x00, 0x00])),
        (-127, bytes([0x81, 0xFF, 0xFF, 0xFF])),
        (32767, bytes([0xFF, 0x7F, 0x00, 0x00])),
        (-32768, bytes([0x00, 0x80, 0xFF, 0xFF])),
        (2147483647, bytes([0xFF, 0xFF, 0xFF, 0x7F])),
        (-2147483648, bytes([0x00, 0x00, 0x00, 0x80])),
    ],
)
class TestFourByteSigned:
    @staticmethod
    def test_dtype_dint(decimal_rep, byte_rep):
        assert DeviceNetDatatype.encode(decimal_rep, DeviceNetDatatype.DINT) == byte_rep
        assert DeviceNetDatatype.decode(byte_rep, DeviceNetDatatype.DINT) == decimal_rep

    @staticmethod
    def test_dtype_time(decimal_rep, byte_rep):
        time_rep = timedelta(milliseconds=decimal_rep)
        assert DeviceNetDatatype.encode(time_rep, DeviceNetDatatype.TIME) == byte_rep
        assert DeviceNetDatatype.decode(byte_rep, DeviceNetDatatype.TIME) == time_rep

    @staticmethod
    def test_dtype_ftime(decimal_rep, byte_rep):
        time_rep = timedelta(microseconds=decimal_rep)
        assert DeviceNetDatatype.encode(time_rep, DeviceNetDatatype.FTIME) == byte_rep
        assert DeviceNetDatatype.decode(byte_rep, DeviceNetDatatype.FTIME) == time_rep


@pytest.mark.parametrize(
    ("decimal_rep", "byte_rep"),
    [
        (127, bytes([0x7F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])),
        (-127, bytes([0x81, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])),
        (32767, bytes([0xFF, 0x7F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])),
        (-32768, bytes([0x00, 0x80, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])),
        (2147483647, bytes([0xFF, 0xFF, 0xFF, 0x7F, 0x00, 0x00, 0x00, 0x00])),
        (-2147483648, bytes([0x00, 0x00, 0x00, 0x80, 0xFF, 0xFF, 0xFF, 0xFF])),
    ],
)
class TestEightByteSigned:
    @staticmethod
    def test_dtype_lint(decimal_rep, byte_rep):
        assert DeviceNetDatatype.encode(decimal_rep, DeviceNetDatatype.LINT) == byte_rep
        assert DeviceNetDatatype.decode(byte_rep, DeviceNetDatatype.LINT) == decimal_rep

    @staticmethod
    def test_dtype_ltime(decimal_rep, byte_rep):
        time_rep = timedelta(microseconds=decimal_rep)
        assert DeviceNetDatatype.encode(time_rep, DeviceNetDatatype.LTIME) == byte_rep
        assert DeviceNetDatatype.decode(byte_rep, DeviceNetDatatype.LTIME) == time_rep

    @staticmethod
    def test_dtype_ntime(decimal_rep, byte_rep):
        time_rep = pd.Timedelta(nanoseconds=decimal_rep)
        assert DeviceNetDatatype.encode(time_rep, DeviceNetDatatype.NTIME) == byte_rep
        assert DeviceNetDatatype.decode(byte_rep, DeviceNetDatatype.NTIME) == time_rep


def test_dtype_eth_mac_addr():
    mac_addr = [0x77, 0xBB, 0x88, 0x01, 0x49, 0x77]
    mac_addr_bytes = bytes([0x77, 0xBB, 0x88, 0x01, 0x49, 0x77])

    assert DeviceNetDatatype.encode(mac_addr, DeviceNetDatatype.ETH_MAC_ADDR) == mac_addr_bytes
    assert DeviceNetDatatype.decode(mac_addr_bytes, DeviceNetDatatype.ETH_MAC_ADDR) == mac_addr

    with pytest.raises(TypeError):
        DeviceNetDatatype.encode(mac_addr[0:5], DeviceNetDatatype.ETH_MAC_ADDR)


@pytest.mark.parametrize(
    ("str_rep", "byte_rep"),
    [
        ("hello", bytes([0x05, 0x68, 0x65, 0x6C, 0x6C, 0x6F])),
        ("", bytes([0x00])),
        (
            "test string",
            bytes([0x0B, 0x74, 0x65, 0x73, 0x74, 0x20, 0x73, 0x74, 0x72, 0x69, 0x6E, 0x67]),
        ),
    ],
)
def test_dtype_short_string(str_rep, byte_rep):
    assert DeviceNetDatatype.encode(str_rep, DeviceNetDatatype.SHORT_STRING) == byte_rep
    assert DeviceNetDatatype.decode(byte_rep, DeviceNetDatatype.SHORT_STRING) == str_rep


@pytest.mark.parametrize(
    ("str_rep", "byte_rep"),
    [
        ("hello", bytes([0x05, 0x00, 0x68, 0x65, 0x6C, 0x6C, 0x6F])),
        ("", bytes([0x00, 0x00])),
        (
            "test string",
            bytes([0x0B, 0x00, 0x74, 0x65, 0x73, 0x74, 0x20, 0x73, 0x74, 0x72, 0x69, 0x6E, 0x67]),
        ),
    ],
)
def test_dtype_string(str_rep, byte_rep):
    assert DeviceNetDatatype.encode(str_rep, DeviceNetDatatype.STRING) == byte_rep
    assert DeviceNetDatatype.decode(byte_rep, DeviceNetDatatype.STRING) == str_rep


@pytest.mark.parametrize(
    ("str_rep", "byte_rep"),
    [
        ("hello", bytes([0x05, 0x00, 0x68, 0x00, 0x65, 0x00, 0x6C, 0x00, 0x6C, 0x00, 0x6F, 0x00])),
        ("", bytes([0x00, 0x00])),
        (
            "test string",
            bytes(
                [
                    0x0B,
                    0x00,
                    0x74,
                    0x00,
                    0x65,
                    0x00,
                    0x73,
                    0x00,
                    0x74,
                    0x00,
                    0x20,
                    0x00,
                    0x73,
                    0x00,
                    0x74,
                    0x00,
                    0x72,
                    0x00,
                    0x69,
                    0x00,
                    0x6E,
                    0x00,
                    0x67,
                    0x00,
                ]
            ),
        ),
    ],
)
def test_dtype_string2(str_rep, byte_rep):
    assert DeviceNetDatatype.encode(str_rep, DeviceNetDatatype.STRING2) == byte_rep
    assert DeviceNetDatatype.decode(byte_rep, DeviceNetDatatype.STRING2) == str_rep
