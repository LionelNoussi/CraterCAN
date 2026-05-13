import time
import struct
import logging
from typing import Optional

from .waveshare_adapter import WaveshareAdapter, CANFrame
from .epos4_constants import CANopenID, SDOCommand, ObjectIndex, OpMode, ControlCommand, StatusBit, DataType


class EPOS4Node:
    def __init__(self, bus: WaveshareAdapter, node_id: int, debug: bool = False):
        assert isinstance(bus, WaveshareAdapter), "bus must be an instance of CraterCAN"
        assert isinstance(node_id, int), "node_id must be an integer"
        assert 1 <= node_id <= 127, "node_id must be between 1 and 127 (CANopen standard)"
        assert isinstance(debug, bool), "debug must be a boolean"

        self.bus = bus
        self.node_id = node_id
        
        self.sdo_tx_id = CANopenID.SDO_TX_BASE + self.node_id
        self.sdo_rx_id = CANopenID.SDO_RX_BASE + self.node_id
        self.heartbeat_id = CANopenID.HEARTBEAT_BASE + self.node_id
        
        self._last_statusword = 0x0000
        self._heartbeat_received = False
        self._sdo_mailboxes = {}
        
        self.logger = logging.getLogger(f"EPOS4_Node_{self.node_id}")
        self.logger.setLevel(logging.DEBUG if debug else logging.INFO)
        if not self.logger.handlers:
            ch = logging.StreamHandler()
            ch.setFormatter(logging.Formatter('%(levelname)s:%(name)s: %(message)s'))
            self.logger.addHandler(ch)

        self.bus.subscribe(self._on_can_frame)

    def _on_can_frame(self, frame: CANFrame) -> None:
        if frame.id == self.heartbeat_id:
            self._heartbeat_received = True
            
        elif frame.id == self.sdo_rx_id:
            cmd = frame.data[0]
            index = frame.data[1] | (frame.data[2] << 8)
            subindex = frame.data[3]
            
            if cmd == SDOCommand.ABORT:
                self.logger.error(f"SDO Abort for Index {hex(index)} Sub {subindex}")
                
            self._sdo_mailboxes[(index, subindex)] = frame.data

    # --- LOW LEVEL SYNCHRONOUS SDO ---

    def sync_write(self, index: ObjectIndex, subindex: int, value: int, dtype: DataType, timeout: float = 0.5) -> bool:
        """Packs a python integer into bytes and sends it via SDO."""
        assert isinstance(index, ObjectIndex), "index must be an ObjectIndex Enum"
        assert isinstance(subindex, int) and 0 <= subindex <= 255, "subindex must be a uint8"
        assert isinstance(value, int), "value must be an integer"
        assert isinstance(dtype, DataType), "dtype must be a DataType Enum"
        assert timeout > 0, "timeout must be positive"

        if dtype.size == 1: cmd = SDOCommand.WRITE_1BYTE
        elif dtype.size == 2: cmd = SDOCommand.WRITE_2BYTE
        elif dtype.size == 4: cmd = SDOCommand.WRITE_4BYTE
        else: raise ValueError("Invalid DataType size for SDO Write.")

        # Let the DataType enum handle the binary packing
        data_bytes = struct.pack(dtype.fmt, value)

        payload = bytearray([cmd, index & 0xFF, (index >> 8) & 0xFF, subindex])
        payload.extend(data_bytes)
        payload.extend(b'\x00' * (8 - len(payload))) 

        # Empty sdo mailbox before sending sdo request
        self._sdo_mailboxes.pop((index.value, subindex), None)
        self.bus.send(self.sdo_tx_id, list(payload))
        
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            response = self._sdo_mailboxes.get((index.value, subindex))
            if response:
                return response[0] == SDOCommand.WRITE_SUCCESS
            time.sleep(0.001)
            
        self.logger.warning(f"Timeout writing to {index.name}")
        return False

    def sync_read(self, index: ObjectIndex, subindex: int, dtype: DataType, timeout: float = 0.5) -> Optional[int]:
        """Requests data via SDO and unpacks it into a python integer."""
        assert isinstance(index, ObjectIndex), "index must be an ObjectIndex Enum"
        assert isinstance(subindex, int) and 0 <= subindex <= 255, "subindex must be a uint8"
        assert isinstance(dtype, DataType), "dtype must be a DataType Enum"
        assert timeout > 0, "timeout must be positive"

        payload = [SDOCommand.READ_REQUEST, index & 0xFF, (index >> 8) & 0xFF, subindex, 0, 0, 0, 0]
        self._sdo_mailboxes.pop((index.value, subindex), None)
        self.bus.send(self.sdo_tx_id, payload)
        
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            response = self._sdo_mailboxes.get((index.value, subindex))
            if response:
                if response[0] in [SDOCommand.READ_RES_4BYTE, SDOCommand.READ_RES_2BYTE, SDOCommand.READ_RES_1BYTE]:
                    # Let the DataType enum handle the binary unpacking
                    return struct.unpack(dtype.fmt, response[4:4+dtype.size])[0]
                return None
            time.sleep(0.001)
            
        self.logger.warning(f"Timeout reading from {index.name}")
        return None

    # --- HIGH LEVEL HELPERS ---

    def wait_for_heartbeat(self, timeout: float = 3.0) -> bool:
        assert timeout > 0, "timeout must be positive"
        self.logger.info("Waiting for node heartbeat...")
        self._heartbeat_received = False
        start_time = time.time()
        while not self._heartbeat_received and (time.time() - start_time) < timeout:
            time.sleep(0.01)
        if self._heartbeat_received:
            self.logger.info("Hearbeat received!")
        return self._heartbeat_received

    def _get_statusword(self) -> Optional[int]:
        val = self.sync_read(ObjectIndex.STATUSWORD, 0x00, DataType.UINT16)
        if val is not None:
            self._last_statusword = val
        return val

    def clear_faults(self) -> bool:
        status = self._get_statusword()
        if status and (status & StatusBit.FAULT):
            self.logger.info("Fault detected. Resetting...")
            ok = self.sync_write(ObjectIndex.CONTROLWORD, 0x00, ControlCommand.FAULT_RESET.value, DataType.UINT16)
            time.sleep(0.1)
            return ok
        return status is not None

    def enable(self) -> bool:
        self.logger.info("Enabling drive...")
        
        if not self.sync_write(ObjectIndex.CONTROLWORD, 0x00, ControlCommand.SHUTDOWN.value, DataType.UINT16):
            return False

        if not self._wait_state(StatusBit.READY_TO_SWITCH_ON):
            return False
            
        if not self.sync_write(ObjectIndex.CONTROLWORD, 0x00, ControlCommand.SWITCH_ON.value, DataType.UINT16):
            return False
        
        if not self._wait_state(StatusBit.SWITCHED_ON):
            return False
            
        if not self.sync_write(ObjectIndex.CONTROLWORD, 0x00, ControlCommand.ENABLE_OPERATION.value, DataType.UINT16):
            return False
        
        if not self._wait_state(StatusBit.OPERATION_ENABLED):
            return False
            
        self.logger.info("Drive ENABLED.")
        return True

    def _wait_state(self, target_bit: StatusBit, timeout: float = 1.0) -> bool:
        assert isinstance(target_bit, StatusBit), "target_bit must be a StatusBit Enum"
        assert timeout > 0, "timeout must be positive"
        start = time.time()
        while (time.time() - start) < timeout:
            sw = self._get_statusword()
            if sw is not None and (sw & target_bit):
                return True
            time.sleep(0.05)
        self.logger.error(f"Failed to reach state: {target_bit.name}")
        return False

    def disable(self) -> bool:
        self.logger.info("Disabling drive...")
        return self.sync_write(ObjectIndex.CONTROLWORD, 0x00, ControlCommand.DISABLE_VOLTAGE.value, DataType.UINT16)

    def set_operation_mode(self, mode: OpMode) -> bool:
        assert isinstance(mode, OpMode), "mode must be an OpMode Enum"
        return self.sync_write(ObjectIndex.OP_MODE, 0x00, mode.value, DataType.INT8)

    # --- VELOCITY MODE ---
    def set_velocity(self, rpm: int) -> bool:
        assert isinstance(rpm, int), "Velocity (rpm) must be an integer"
        return self.sync_write(ObjectIndex.TARGET_VELOCITY, 0x00, rpm, DataType.INT32)

    def get_actual_velocity(self) -> Optional[int]:
        return self.sync_read(ObjectIndex.VELOCITY_ACTUAL, 0x00, DataType.INT32)

    # --- POSITION MODE ---
    def move_position_relative(self, steps: int) -> bool:
        assert isinstance(steps, int), "Steps must be an integer"
        
        if not self.sync_write(ObjectIndex.TARGET_POSITION, 0x00, steps, DataType.INT32):
            return False
            
        if not self.sync_write(ObjectIndex.CONTROLWORD, 0x00, ControlCommand.POS_REL_PREPARE.value, DataType.UINT16):
            return False
        
        time.sleep(0.01)
        
        return self.sync_write(ObjectIndex.CONTROLWORD, 0x00, ControlCommand.POS_REL_EXECUTE.value, DataType.UINT16)

    def get_actual_position(self) -> Optional[int]:
        return self.sync_read(ObjectIndex.POSITION_ACTUAL, 0x00, DataType.INT32)