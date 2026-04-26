from src.crater_can import CraterCAN, CANFrame
import time

def on_msg(frame: CANFrame) -> None:
    # Extremely clean access
    print(f"ID: {hex(frame.id)} | Payload: {frame.data.hex()}")

bus = CraterCAN('/dev/cu.usbserial-120')
bus.start(on_msg)

try:
    while True:
        bus.send(0x123, [0xAA, 0xBB])
        time.sleep(1)
except KeyboardInterrupt:
    bus.stop()