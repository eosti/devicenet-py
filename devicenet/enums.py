from enum import IntEnum

from devicenet.dtypes import DeviceNetDatatype


class DeviceNetMessageGroup(IntEnum):
    """Message group values follow Table 2 for explicit connection requests"""

    MESSAGE_GROUP_1 = 0
    MESSAGE_GROUP_2 = 1
    MESSAGE_GROUP_3 = 3
    MESSAGE_GROUP_4 = 2


class DeviceNetBodyFormat(IntEnum):
    DEVICENET_8_8 = 0
    DEVICENET_8_16 = 1
    DEVICENET_16_16 = 2
    DEVICENET_16_8 = 3
    DEVICENET_CIP_PATH = 4


class DeviceNetState(IntEnum):
    COMMUNICATION_FAULT = 0
    OFFLINE = 1
    CONNECTING = 2
    ONLINE = 3


class DeviceNetFragmentationType(IntEnum):
    FIRST_FRAGMENT = 0
    MIDDLE_FRAGMENT = 1
    LAST_FRAGMENT = 2
    FRAGMENT_ACKNOWLEDGE = 3


class DeviceNetServiceCode(IntEnum):
    """IEC 61158-6-2:2014 Table 172"""

    GET_ATTRIBUTE_ALL = 0x01
    SET_ATTRIBUTE_ALL = 0x02
    GET_ATTRIBUTE_LIST = 0x03
    SET_ATTRIBUTE_LIST = 0x04
    RESET = 0x05
    START = 0x06
    STOP = 0x07
    CREATE = 0x08
    DELETE = 0x09
    APPLY_ATTRIBUTES = 0x0D
    GET_ATTRIBUTE_SINGLE = 0x0E
    SET_ATTRIBUTE_SINGLE = 0x10
    FIND_NEXT_OBJECT_INSTANCE = 0x11
    RESTORE = 0x15
    SAVE = 0x16
    NOP = 0x17
    GET_MEMBER = 0x18
    SET_MEMBER = 0x19
    INSERT_MEMBER = 0x1A
    REMOVE_MEMBER = 0x1B
    GROUP_SYNC = 0x1C


class AttributeEnum(IntEnum):
    def __init__(self, value: int, dtype: DeviceNetDatatype):
        self.val = (value,)
        self.dtype = dtype

    def __new__(cls, value: int, dtype: DeviceNetDatatype):
        member = object.__new__(cls)
        member._value_ = value
        member.dtype = dtype
        return member


class DeviceNetConnectionObjectAttributes(AttributeEnum):
    """IEC 61158-6-2:2014 Table 137"""

    STATE = 1, DeviceNetDatatype.USINT
    INSTANCE_TYPE = 2, DeviceNetDatatype.USINT
    TRANSPORTCLASS_TRIGGER = 3, DeviceNetDatatype.SWORD
    CP23_PRODUCED_CONNECTION_ID = 4, DeviceNetDatatype.UINT
    CP23_CONSUMED_CONNECTION_ID = 5, DeviceNetDatatype.UINT
    CP23_INITIAL_COMMUNICATION_CHARACTERISTICS = 6, DeviceNetDatatype.SWORD
    PRODUCED_CONNECTION_SIZE = 7, DeviceNetDatatype.UINT
    CONSUMED_CONNECTION_SIZE = 8, DeviceNetDatatype.UINT
    EXPECTED_PACKET_RATE = 9, DeviceNetDatatype.UINT
    CPF2_PRODUCED_CONNECTION_ID = 10, DeviceNetDatatype.UDINT
    CPF2_CONSUMED_CONNECTION_ID = 11, DeviceNetDatatype.UDINT
    WATCHDOG_TIMEOUT_ACTION = 12, DeviceNetDatatype.USINT
    PRODUCED_CONNECTION_PATH_LENGTH = 13, DeviceNetDatatype.UINT
    PRODUCED_CONNECTION_PATH = 14, DeviceNetDatatype.EPATH
    CONSUMED_CONNECTION_PATH_LENGTH = 15, DeviceNetDatatype.UINT
    CONSUMED_CONNECTION_ATH = 16, DeviceNetDatatype.EPATH
    PRODUCTION_INHIBIT_TIME = 17, DeviceNetDatatype.UINT
    CONNECTION_TIMEOUT_MULTIPLIER = 18, DeviceNetDatatype.USINT
    CONNECTION_BINDING_LIST = 19, DeviceNetDatatype.STRUCT_UINT
