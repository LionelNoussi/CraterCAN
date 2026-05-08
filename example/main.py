from crater_can import CraterCAN, CANFrame
import time

def on_msg(frame: CANFrame) -> None:
    # Extremely clean access
    print(f"Received | ID: {hex(frame.id)} | Payload: {frame.data.hex()}")


# TODO Change this to the port on your host machine
PORT = '/dev/cu.usbserial-140'

def main():
    bus = CraterCAN(PORT)
    bus.listen(on_msg)
    print(f"CAN communication started on {PORT}. Press Ctrl+C to stop.")

    try:
        while True:
            # Example heartbeat to the ESP32
            bus.send(0x123, [0xAA, 0xBB])
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        bus.stop()

if __name__ == "__main__":
    main()
    