from crater_can import CraterCAN, CANFrame
from enum import IntEnum
import time

# ============================================================================
# DATA STRUCTURES & DICTIONARIES
# ============================================================================

class ObjectIndex(IntEnum):
    """CANopen Object Dictionary Indexes for EPOS4"""
    DEVICE_TYPE = 0x1000
    ERROR_CODE = 0x603F
    CONTROLWORD = 0x6040
    STATUSWORD = 0x6041
    MODE_OF_OPERATION = 0x6060
    POSITION_ACTUAL = 0x6064
    VELOCITY_DEMAND = 0x606B
    VELOCITY_ACTUAL = 0x606C
    TARGET_VELOCITY = 0x60FF

class OpMode(IntEnum):
    """CiA 402 Modes of Operation"""
    PROFILE_POSITION = 1
    PROFILE_VELOCITY = 3
    HOMING = 6
    CYCLIC_SYNC_POSITION = 8
    CYCLIC_SYNC_VELOCITY = 9

class ControlCommand(IntEnum):
    """Controlword bit-patterns to transition the CiA 402 State Machine"""
    SHUTDOWN = 0x0006          # Move to 'Ready to Switch On'
    SWITCH_ON = 0x0007         # Move to 'Switched On'
    ENABLE_OPERATION = 0x000F  # Energize motor
    DISABLE_VOLTAGE = 0x0000   # Emergency stop / Coast
    QUICK_STOP = 0x0002        # Active brake
    FAULT_RESET = 0x0080       # Clears faults (0->1 transition)

# ============================================================================
# 2. THE BACKGROUND LIBRARY (EPOS4 CLASS)
# ============================================================================

class EPOS4:
    def __init__(self, port: str, node_id: int = 1):
        self.port = port
        self.node_id = node_id
        
        # CANopen COB-IDs
        self.sdo_tx_id = 0x600 + self.node_id  # PC -> EPOS4
        self.sdo_rx_id = 0x580 + self.node_id  # EPOS4 -> PC
        self.pdo_status_id = 0x180 + self.node_id # Typical PDO1 Tx
        
        # State Tracking
        self.statusword = 0x0000
        
        # Initialize CAN
        print(f"[SYSTEM] Initializing CAN adapter on {port}...")
        self.bus = CraterCAN(port)
        self.bus.listen(self._on_message)

    def _on_message(self, frame: CANFrame) -> None:
        # 1. Handle PDO (Automatic broadcast from EPOS4)
        if frame.id == self.pdo_status_id or frame.id == 0x1a0: 
            # The Statusword is the first 2 bytes of the PDO
            self.statusword = int.from_bytes(frame.data[0:2], 'little')
            # print(f"DEBUG: Statusword updated via PDO: {hex(self.statusword)}")

        # 2. Handle SDO (Direct responses to our questions)
        elif frame.id == self.sdo_rx_id:
            cmd = frame.data[0]
            index = frame.data[1] + (frame.data[2] << 8)
            
            # If we asked for Statusword specifically (Read request)
            if index == ObjectIndex.STATUSWORD and cmd in [0x4B, 0x43]:
                self.statusword = int.from_bytes(frame.data[4:6], 'little')

    # --- LOW LEVEL CANOPEN FUNCTIONS ---

    def nmt_start(self):
        """Puts the node into Operational State (Starts PDO broadcasts)"""
        self.bus.send(0x000, [0x01, self.node_id])

    def write_sdo(self, index: int, subindex: int, data_bytes: bytes):
        """Builds and sends an SDO Download Request (Write to EPOS)"""
        length = len(data_bytes)
        
        # Determine the correct Command Specifier (Byte 0) based on data length
        if length == 1: cmd = 0x2F
        elif length == 2: cmd = 0x2B
        elif length == 4: cmd = 0x23
        else: raise ValueError("Data must be 1, 2, or 4 bytes.")

        # Pack payload: [Cmd, IndexLow, IndexHigh, SubIndex, Data0, Data1, Data2, Data3]
        idx_low = index & 0xFF
        idx_high = (index >> 8) & 0xFF
        
        payload = [cmd, idx_low, idx_high, subindex]
        payload.extend(list(data_bytes))
        payload.extend([0x00] * (4 - length)) # Pad to 8 bytes

        self.bus.send(self.sdo_tx_id, payload)

    def read_sdo(self, index: int, subindex: int = 0):
        """Requests data from the EPOS. Handled asynchronously by the listener."""
        idx_low = index & 0xFF
        idx_high = (index >> 8) & 0xFF
        payload = [0x40, idx_low, idx_high, subindex, 0x00, 0x00, 0x00, 0x00]
        self.bus.send(self.sdo_tx_id, payload)

    # --- HIGH LEVEL MOTION FUNCTIONS ---

    def reset_fault(self):
        """Clears existing faults by toggling Bit 7 in the Controlword."""
        print("[DRIVE] Resetting faults...")
        # Send Fault Reset (0x80)
        self.write_sdo(ObjectIndex.CONTROLWORD, 0x00, ControlCommand.FAULT_RESET.value.to_bytes(2, 'little'))
        time.sleep(0.5)
        # Drop it back to 0 so it can be triggered again later
        self.write_sdo(ObjectIndex.CONTROLWORD, 0x00, (0x0000).to_bytes(2, 'little'))
        time.sleep(0.1)

    def set_mode(self, mode: OpMode):
        """Changes the CiA 402 Operating Mode"""
        print(f"[DRIVE] Setting Mode to: {mode.name}")
        self.write_sdo(ObjectIndex.MODE_OF_OPERATION, 0x00, mode.value.to_bytes(1, 'little'))
        time.sleep(0.1)

    def enable(self):
        """Safely navigates the CiA 402 State Machine to energize the motor."""
        print("[DRIVE] Running Enable Sequence...")
        
        # Shutdown -> Switch On -> Enable
        for cmd in [ControlCommand.SHUTDOWN, ControlCommand.SWITCH_ON, ControlCommand.ENABLE_OPERATION]:
            self.write_sdo(ObjectIndex.CONTROLWORD, 0x00, cmd.value.to_bytes(2, 'little'))
            time.sleep(0.1)

        # Corrected Check: Bit 0, 1, 2, and 3 should be 1. Bit 3 (Fault) should be 0.
        # 0x000F masks the ready/enabled bits.
        if (self.statusword & 0x000F) == 0x000F:
            print(f"[DRIVE] Operation Enabled. Status: {hex(self.statusword)}")
        else:
            print(f"[WARN] State is {hex(self.statusword)}. Check STO/Power.")

    def disable(self):
        """Disables the power stage and lets the motor coast."""
        print("[DRIVE] Disabling drive...")
        self.write_sdo(ObjectIndex.CONTROLWORD, 0x00, ControlCommand.DISABLE_VOLTAGE.value.to_bytes(2, 'little'))

    def set_velocity(self, rpm: int):
        """Sets Target Velocity and explicitly clears the Halt bit."""
        print(f"[MOTION] Commanding Velocity: {rpm} RPM")
        
        # 1. Set the Velocity
        data = rpm.to_bytes(4, byteorder='little', signed=True)
        self.write_sdo(ObjectIndex.TARGET_VELOCITY, 0x00, data)
        
        # 2. Force Controlword to 0x000F (Ensures Bit 8 'Halt' is 0)
        self.write_sdo(ObjectIndex.CONTROLWORD, 0x00, (0x000F).to_bytes(2, 'little'))

    def stop_bus(self):
        """Cleans up the serial connection."""
        self.bus.stop()
        print("[SYSTEM] CAN bus closed.")
