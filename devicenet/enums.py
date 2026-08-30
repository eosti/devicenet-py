from enum import IntEnum


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
