# src/crater_can/__init__.py

from .waveshare_adapter import WaveshareAdapter, CANFrame
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
    "WaveshareAdapter",
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