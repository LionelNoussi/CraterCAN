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


class WaveshareAdapter:
    
    def __init__(self, port: str, baud: int = 2000000) -> None:
        try:
            self.ser: serial.Serial = serial.Serial(port, baud, timeout=0.01)
        except OSError:
            # This allows socat/pty simulated serial port
            self.ser: serial.Serial = serial.Serial(port, timeout=0.01)
        
        self._callbacks: List[Callable[[CANFrame], None]] = []
        self._running: bool = False

    def send(self, msg_id: int, data: List[int]) -> None:
        """Packs and sends a 20-byte Waveshare binary frame."""
        # [Header(2), Type(1), Subtype(1), Command(1)]
        frame = bytearray([0xAA, 0x55, 0x01, 0x01, 0x00]) # Waveshare and CAN Header
        frame += struct.pack('<I', msg_id)  # Message ID
        frame.append(len(data)) # Message length
        frame += bytes(data).ljust(8, b'\x00')  # Data
        frame.append(0x00)  # Reserved padding
        frame.append(sum(frame[2:]) & 0xFF)  # Checksum
        self.ser.write(frame)

    def _listen(self) -> None:
        """Internal background loop to parse incoming binary stream."""
        while self._running:
            if self.ser.in_waiting >= 20:
                if self.ser.read(1) == b'\xAA' and self.ser.read(1) == b'\x55':
                    body: bytes = self.ser.read(18)
                    if len(body) == 18 and len(self._callbacks) > 0:
                        # Wrap the raw data in our DataClass
                        msg_id: int = struct.unpack('<I', body[3:7])[0]
                        dlc: int = body[7]
                        frame = CANFrame(id=msg_id, data=body[8:8+dlc])
                        for callback in self._callbacks:
                            callback(frame)
            time.sleep(0.001)

    def listen(self, callback_func: Callable[[CANFrame], None] | None = None) -> None:
        """Starts the background thread and optionally adds a callback."""
        if not self._running:
            if callback_func is not None:
                self._callbacks.append(callback_func)
            self._running = True
            thread = threading.Thread(target=self._listen, daemon=True)
            thread.start()

    def subscribe(self, callback_func: Callable[[CANFrame], None]) -> None:
        """Adds a callback to the callback stack."""
        if callback_func not in self._callbacks:
            self._callbacks.append(callback_func)

    def unsubscribe(self, callback_func: Callable[[CANFrame], None]) -> None:
        """Removes a callback from the callback stack."""
        if callback_func in self._callbacks:
            self._callbacks.remove(callback_func)

    def stop_listening(self) -> None:
        """Stops listening by deactivating the background thread."""
        self._running = False

    def close(self) -> None:
        """Stops listening and closes the serial connection."""
        self._running = False
        self.ser.close()