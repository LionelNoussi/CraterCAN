# src/crater_can/epos4_constants.py

from enum import IntEnum, IntFlag, Enum


class CANopenID(IntEnum):
    NMT_SERVICE = 0x000
    SDO_TX_BASE = 0x600  # PC -> Drive
    SDO_RX_BASE = 0x580  # Drive -> PC
    HEARTBEAT_BASE = 0x700
    PDO1_TX_BASE = 0x180 # Statusword broadcast


class SDOCommand(IntEnum):
    # Write Requests (PC -> Drive)
    WRITE_1BYTE = 0x2F
    WRITE_2BYTE = 0x2B
    WRITE_4BYTE = 0x23
    # Read Requests (PC -> Drive)
    READ_REQUEST = 0x40
    # Responses (Drive -> PC)
    WRITE_SUCCESS = 0x60
    READ_RES_1BYTE = 0x4F
    READ_RES_2BYTE = 0x4B
    READ_RES_4BYTE = 0x43
    ABORT = 0x80


class ObjectIndex(IntEnum):
    # System
    DEVICE_TYPE = 0x1000
    ERROR_CODE = 0x603F
    CONTROLWORD = 0x6040
    STATUSWORD = 0x6041
    OP_MODE = 0x6060
    
    # Position
    POSITION_ACTUAL = 0x6064
    TARGET_POSITION = 0x607A
    PROFILE_VELOCITY = 0x6081
    PROFILE_ACCELERATION = 0x6083
    PROFILE_DECELERATION = 0x6084
    
    # Velocity
    VELOCITY_DEMAND = 0x606B
    VELOCITY_ACTUAL = 0x606C
    TARGET_VELOCITY = 0x60FF


class OpMode(IntEnum):
    PROFILE_POSITION = 1
    PROFILE_VELOCITY = 3
    HOMING = 6
    CYCLIC_SYNC_POSITION = 8
    CYCLIC_SYNC_VELOCITY = 9


class ControlCommand(IntEnum):
    SHUTDOWN = 0x0006
    SWITCH_ON = 0x0007
    ENABLE_OPERATION = 0x000F
    DISABLE_VOLTAGE = 0x0000
    QUICK_STOP = 0x0002
    FAULT_RESET = 0x0080
    
    # Profile Position Specifics
    # Bits: Enable(0x0F) | Relative(0x40) | NewSetpoint(0x10)
    POS_REL_PREPARE = 0x004F 
    POS_REL_EXECUTE = 0x005F


class StatusBit(IntFlag):
    READY_TO_SWITCH_ON = 0x0001
    SWITCHED_ON = 0x0002
    OPERATION_ENABLED = 0x0004
    FAULT = 0x0008
    VOLTAGE_ENABLED = 0x0010
    QUICK_STOP = 0x0020
    SWITCH_ON_DISABLED = 0x0040
    WARNING = 0x0080
    TARGET_REACHED = 0x0400


class DataType(Enum):
    """Maps CANopen data types to Python struct formats and byte lengths."""
    INT8 = ('<b', 1)
    UINT8 = ('<B', 1)
    INT16 = ('<h', 2)
    UINT16 = ('<H', 2)
    INT32 = ('<i', 4)
    UINT32 = ('<I', 4)

    @property
    def fmt(self) -> str:
        return self.value[0]

    @property
    def size(self) -> int:
        return self.value[1]