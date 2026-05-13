from crater_can import CraterCAN, CANFrame
import time
import argparse


def on_msg(frame: CANFrame) -> None:
    print(f"Received | ID: {hex(frame.id)} | Payload: {frame.data.hex()}")


def main(port):

    bus = CraterCAN(port)
    bus.listen(on_msg)

    print(f"CAN communication started on {port}. Press Ctrl+C to stop.")

    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        bus.close()


if __name__ == "__main__":

    # NOTE change default port to match your machine or provide it with --port
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=str, default="/dev/ttys008")
    port = parser.parse_args().port

    main(port)
    