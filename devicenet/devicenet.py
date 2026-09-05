import logging
import time
from typing import Any

import bitstring
from can import Message
from can.interface import BusABC

from devicenet.cid import DeviceNetCID
from devicenet.dtypes import DeviceNetDatatype
from devicenet.enums import (
    AttributeEnum,
    DeviceNetBodyFormat,
    DeviceNetMessageGroup,
    DeviceNetServiceCode,
    DeviceNetState,
)
from devicenet.fields import DeviceNetAllocationChoiceByte
from devicenet.helpers import CanFilter
from devicenet.messages import (
    DeviceNetAllocateMasterSlaveConnectionRequestMessage,
    DeviceNetAllocateMasterSlaveConnectionResponseMessage,
    DeviceNetDataMessage,
    DeviceNetDuplicateMACIDCheckMessage,
    DeviceNetEmptyMessage,
    DeviceNetExplicitMessageGenericService,
    DeviceNetExplicitMessagingConnectionRequestMessage,
    DeviceNetExplicitMessagingConnectionResponseMessage,
    DeviceNetExplicitRequestMessage,
    DeviceNetMessage,
)

logger = logging.getLogger(__name__)
bitstring.options.lsb0 = True


class DeviceNet:
    def __init__(
        self,
        bus: BusABC,
        mac_id: int,
        vendor_id: int = 0,
        serial_number: int = 0,
        port_number: int = 0,
    ) -> None:
        self.bus = bus
        self.mac_id = mac_id
        self.vendor_id = vendor_id
        self.serial_number = serial_number
        self.port_number = port_number

        # Callbacks come in the form of python-can filters, with the "callback" key.
        self.callbacks: list[CanFilter] = []
        self.fallback_callback = self._fallback_callback

        self.state = DeviceNetState.OFFLINE

        self.handle_messages()

    def register_callback(self, filter: CanFilter) -> None:
        if filter in self.callbacks:
            raise ValueError("Callback already exists")
        self.callbacks.append(filter)

    def deregister_callback(self, filter: CanFilter) -> None:
        self.callbacks.remove(filter)

    def handle_messages(self, timeout=0.1) -> None:
        while 1:
            resp = self.recv(timeout=timeout)
            if resp is None:
                return
            cid, data = resp
            callback_run = False
            for f in self.callbacks:
                if cid.pack() & f.mask == f.id & f.mask:
                    f.callback(cid, data)
                    callback_run = True

            if callback_run is False:
                self.fallback_callback(cid, data)

    @staticmethod
    def _fallback_callback(cid: DeviceNetCID, data: bytes) -> None:
        logger.debug("Fallback callback reached for cid %s", cid)

    def recv(self, timeout=0.1) -> tuple[DeviceNetCID, bytes] | None:
        msg = self.bus.recv(timeout=timeout)
        if msg is None:
            return None
        logger.debug("RX: %s", msg)
        if msg.is_extended_id or msg.is_fd:
            logger.error("Message has unsupported parameters")
            return None

        cid = DeviceNetCID.unpack(msg.arbitration_id)
        logger.debug(cid)

        return (cid, bytes(msg.data))

    def send(self, cid: DeviceNetCID, msg: DeviceNetMessage) -> None:
        for d in msg.pack():
            frame = Message(arbitration_id=cid.pack(), data=d, is_extended_id=False, is_fd=False)
            self.bus.send(frame)
            logger.debug("TX: %s", frame)

    def open_explicit_messaging_connection_request(
        self,
        dest_mac_id: int,
        body_format: DeviceNetBodyFormat,
        group_select: DeviceNetMessageGroup,
        source_message_id: int,
    ) -> bool:
        """Request establishment of a connection between two nodes.

        This process is defined in IEC 62026-3:2014, section 5.2.1.5.2.
        """
        body = DeviceNetExplicitMessagingConnectionRequestMessage(
            dest_mac=dest_mac_id,
            body_format=body_format,
            group_select=group_select,
            source_message_id=source_message_id,
        )
        cid = DeviceNetCID(
            message_group=DeviceNetMessageGroup.MESSAGE_GROUP_3,
            message_id=0x06,
            mac_id=self.mac_id,
        )
        self.send(cid, body)

        resp = None

        def handler(cid, data) -> None:
            nonlocal resp
            resp = data

        resp_cid = DeviceNetCID(
            message_group=DeviceNetMessageGroup.MESSAGE_GROUP_3,
            message_id=0x05,
            mac_id=dest_mac_id,
        )
        filter = CanFilter(id=resp_cid.pack(), mask=0x63F, callback=handler)
        self.register_callback(filter)
        self.handle_messages()
        self.deregister_callback(filter)

        if resp is None:
            logger.error("No response to connection request")
            return False

        DeviceNetExplicitMessagingConnectionResponseMessage.unpack(resp)
        # TODO: not sure what to do now
        return True

    def duplicate_mac_id_check_request(self, check_collisions=True) -> bool:
        """Sends a duplicate MAC ID check request and handles the response.

        This process is defined in IEC 62026-3:2014, section 5.2.7.

        Args:
            check_collision: whether to check for collisions immediately,
                set to False for quick connect.

        Returns:
            bool: True if no collision detected, False otherwise.

        """
        cid = DeviceNetCID.duplicate_mac_id_check(dest_mac=self.mac_id)
        data = DeviceNetDuplicateMACIDCheckMessage(
            physical_port_number=self.port_number,
            vendor_id=self.vendor_id,
            serial_number=self.serial_number,
        )
        self.send(cid, data)

        if not check_collisions:
            return True

        mac_collision = None

        def handler(cid, data) -> None:
            nonlocal mac_collision
            mac_collision = data

        filter = CanFilter(id=cid.pack(), mask=0x7FF, callback=handler)
        self.register_callback(filter)
        self.handle_messages()
        self.deregister_callback(filter)

        if mac_collision is None:
            logger.info("No MAC collision detected for %s", self.mac_id)
            return True
        collision_data = DeviceNetDuplicateMACIDCheckMessage.unpack(mac_collision)
        if collision_data.is_response is False:
            raise RuntimeError("Received MAC check response but R/R flag not set")

        logger.warning(
            "MAC collision detected with vid=%s sn=%s",
            hex(collision_data.vendor_id),
            hex(collision_data.serial_number),
        )
        return False

    def add_mac_check_callback(self) -> None:
        cid = DeviceNetCID.duplicate_mac_id_check(dest_mac=self.mac_id)
        filter = CanFilter(id=cid.pack(), mask=0x7FF, callback=self.mac_id_check_callback)
        self.register_callback(filter)

    def mac_id_check_callback(self, cid, data) -> None:
        check = DeviceNetDuplicateMACIDCheckMessage.unpack(data)
        if check.is_response is False:
            # We respond to say that this MAC is already in use
            logger.info(
                "MAC collision request from vid=%s sn=%s",
                hex(check.vendor_id),
                hex(check.serial_number),
            )
            cid = DeviceNetCID.duplicate_mac_id_check(dest_mac=self.mac_id)
            data = DeviceNetDuplicateMACIDCheckMessage(
                physical_port_number=self.port_number,
                vendor_id=self.vendor_id,
                serial_number=self.serial_number,
                is_response=True,
            )
            self.send(cid, data)
        else:
            # Late response to our MAC ID check message
            self.state = DeviceNetState.COMMUNICATION_FAULT
            logger.warning(
                "MAC collision detected with vid=%s sn=%s",
                hex(check.vendor_id),
                hex(check.serial_number),
            )
            raise RuntimeError("MAC already in use, cannot connect to bus.")

    def connect(self, quick_connect=False) -> None:
        """Connects to a DeviceNet bus.

        This process is defined in IEC 62026-3:2014, section 5.4.2.

        Args:
            quick_connect: don't wait for a collision response

        """
        if self.state == DeviceNetState.ONLINE:
            return

        logger.info("Performing MAC ID collision check for MAC ID %s", hex(self.mac_id))
        self.state = DeviceNetState.CONNECTING
        if quick_connect:
            self.duplicate_mac_id_check_request(check_collisions=False)
            self.state = DeviceNetState.ONLINE
            logger.info("Connected to bus as %s (quick)", hex(self.mac_id))
            self.add_mac_check_callback()
            return

        if self.duplicate_mac_id_check_request() is False:
            self.state = DeviceNetState.COMMUNICATION_FAULT
            raise RuntimeError("MAC already in use, cannot connect to bus.")

        logger.info("Waiting 1s before checking for duplicate MAC IDs again...")
        time.sleep(1)

        if self.duplicate_mac_id_check_request() is False:
            self.state = DeviceNetState.COMMUNICATION_FAULT
            raise RuntimeError("MAC already in use, cannot connect to bus.")

        self.state = DeviceNetState.ONLINE
        logger.info("Connected to bus as %s", hex(self.mac_id))
        self.add_mac_check_callback()

    def master_slave_connect(
        self, dest_mac_id: int, allocation_choice: DeviceNetAllocationChoiceByte
    ) -> DeviceNetBodyFormat:
        body = DeviceNetAllocateMasterSlaveConnectionRequestMessage(
            mac_id=self.mac_id,
            allocation_choice=allocation_choice,
            allocator_id=self.mac_id,
        )
        cid = DeviceNetCID.master_explicit_request(dest_mac=dest_mac_id)
        self.send(cid, body)

        resp = None

        def handler(cid, data) -> None:
            nonlocal resp
            resp = data

        resp_cid = DeviceNetCID.slave_explicit_response(source_mac=dest_mac_id)
        filter = CanFilter(id=resp_cid.pack(), mask=0x7FF, callback=handler)
        self.register_callback(filter)
        self.handle_messages()
        self.deregister_callback(filter)

        if resp is None:
            raise RuntimeError("No response to connection request")

        connection_response = DeviceNetAllocateMasterSlaveConnectionResponseMessage.unpack(resp)

        return connection_response.message_body_format

    def get_attribute_single(
        self,
        dest_mac_id: int,
        attribute: AttributeEnum,
        body_format: DeviceNetBodyFormat = DeviceNetBodyFormat.DEVICENET_8_8,
    ) -> bytes:
        body = DeviceNetExplicitRequestMessage(
            service_code=DeviceNetServiceCode.GET_ATTRIBUTE_SINGLE,
            is_response=False,
            mac_id=self.mac_id,
            class_id=5,
            instance_id=2,
            body_format=body_format,
            message=bytes([attribute.value]),
        )
        cid = DeviceNetCID.master_explicit_request(dest_mac=dest_mac_id)
        self.send(cid, body)

        resp = None

        def handler(cid, data) -> None:
            nonlocal resp
            resp = data

        resp_cid = DeviceNetCID.slave_explicit_response(source_mac=dest_mac_id)
        filter = CanFilter(id=resp_cid.pack(), mask=0x7FF, callback=handler)
        self.register_callback(filter)
        self.handle_messages()
        self.deregister_callback(filter)

        if resp is None:
            raise RuntimeError("No response to get attribute single request")

        resp_data = DeviceNetExplicitMessageGenericService.unpack(resp)
        if resp_data.service_code != DeviceNetServiceCode.GET_ATTRIBUTE_SINGLE:
            logger.debug(resp_data)
            raise RuntimeError("Response service code does not match")

        if resp_data.message is None:
            return b""

        return DeviceNetDatatype.decode(resp_data.message, attribute.dtype)

    def set_attribute_single(
        self,
        dest_mac_id: int,
        attribute: AttributeEnum,
        val: Any,
        body_format: DeviceNetBodyFormat = DeviceNetBodyFormat.DEVICENET_8_8,
    ) -> None:
        payload = DeviceNetDatatype.encode(val, attribute.dtype)
        body = DeviceNetExplicitRequestMessage(
            service_code=DeviceNetServiceCode.SET_ATTRIBUTE_SINGLE,
            is_response=False,
            mac_id=self.mac_id,
            class_id=5,
            instance_id=2,
            body_format=body_format,
            message=bytes([attribute.value]) + payload,
        )

        cid = DeviceNetCID.master_explicit_request(dest_mac=dest_mac_id)
        self.send(cid, body)

        resp = None

        def handler(cid, data) -> None:
            nonlocal resp
            resp = data

        resp_cid = DeviceNetCID.slave_explicit_response(source_mac=dest_mac_id)
        filter = CanFilter(id=resp_cid.pack(), mask=0x7FF, callback=handler)
        self.register_callback(filter)
        self.handle_messages()
        self.deregister_callback(filter)

        if resp is None:
            raise RuntimeError("No response to set attribute single request")

        resp_data = DeviceNetExplicitMessageGenericService.unpack(resp)
        if resp_data.service_code != DeviceNetServiceCode.SET_ATTRIBUTE_SINGLE:
            logger.debug(resp_data)
            raise RuntimeError("Response service code does not match")
        if resp_data.message != payload:
            logger.info("Set value differs: sent %s but received %s", payload, resp_data.message)

    def poll_io(self, dest_mac_id: int, val: bytes | None = None):
        cid = DeviceNetCID.master_poll_command_or_change_of_state_or_cyclic(dest_mac=dest_mac_id)
        if val is not None:
            body = DeviceNetDataMessage(val)
        else:
            # read only
            body = DeviceNetEmptyMessage()

        self.send(cid, body)

        resp = None

        def handler(cid, data) -> None:
            nonlocal resp
            resp = data

        resp_cid = DeviceNetCID.slave_poll_response_or_ack(source_mac=dest_mac_id)
        filter = CanFilter(id=resp_cid.pack(), mask=0x7FF, callback=handler)
        self.register_callback(filter)
        self.handle_messages()
        self.deregister_callback(filter)

        if resp is None:
            raise RuntimeError("No response to poll io")

        return resp
