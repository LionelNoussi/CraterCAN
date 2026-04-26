import serial
import struct
import threading
import time
from dataclasses import dataclass
from typing import List, Callable, Optional

@dataclass(frozen=True)
class CANFrame:
    """Immutable structure representing a single CAN message."""
    id: int
    data: bytes

    def __repr__(self) -> str:
        return f"CANFrame(id={hex(self.id)}, data={self.data.hex(' ')})"

class CraterCAN:
    def __init__(self, port: str, baud: int = 2000000) -> None:
        self.ser: serial.Serial = serial.Serial(port, baud, timeout=0.01)
        self._callback: Optional[Callable[[CANFrame], None]] = None
        self._running: bool = False

    def send(self, msg_id: int, data: List[int]) -> None:
        """Packs and sends a 20-byte Waveshare binary frame."""
        # [Header(2), Type(1), Subtype(1), Command(1)]
        frame = bytearray([0xAA, 0x55, 0x01, 0x01, 0x00])
        frame += struct.pack('<I', msg_id)
        frame.append(len(data))
        frame += bytes(data).ljust(8, b'\x00')
        frame.append(0x00)  # Reserved padding
        frame.append(sum(frame[2:]) & 0xFF)  # Checksum
        self.ser.write(frame)

    def _listen(self) -> None:
        """Internal background loop to parse incoming binary stream."""
        while self._running:
            if self.ser.in_waiting >= 20:
                if self.ser.read(1) == b'\xAA' and self.ser.read(1) == b'\x55':
                    body: bytes = self.ser.read(18)
                    if len(body) == 18 and self._callback:
                        msg_id: int = struct.unpack('<I', body[3:7])[0]
                        dlc: int = body[7]
                        # Wrap the raw data in our DataClass
                        frame = CANFrame(id=msg_id, data=body[8:8+dlc])
                        self._callback(frame)
            time.sleep(0.001)

    def start(self, callback_func: Callable[[CANFrame], None]) -> None:
        """Starts the background thread and assigns the callback."""
        self._callback = callback_func
        self._running = True
        thread = threading.Thread(target=self._listen, daemon=True)
        thread.start()

    def stop(self) -> None:
        """Cleans up the background thread and serial connection."""
        self._running = False
        self.ser.close()