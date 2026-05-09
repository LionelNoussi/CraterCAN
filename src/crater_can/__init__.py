# src/crater_can/__init__.py

from .adapter import CraterCAN, CANFrame
from .epos4_constants import (
    ObjectIndex, 
    OpMode, 
    StatusBit, 
    ControlCommand,
    DataType
)
from .epos4_controller import EPOS4Node
from .epos4_simulator import EPOS4Simulator, CraterSimulatorBus # Added these

__all__ = [
    "CraterCAN",
    "CANFrame",
    "EPOS4Node",
    "ObjectIndex",
    "OpMode",
    "StatusBit",
    "ControlCommand",
    "DataType",
    "EPOS4Simulator",     # Added
    "CraterSimulatorBus"  # Added
]