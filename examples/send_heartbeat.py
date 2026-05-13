from crater_can import WaveshareAdapter, CANFrame
import time
import argparse


def on_msg(frame: CANFrame) -> None:
    print(f"Received | ID: {hex(frame.id)} | Payload: {frame.data.hex()}")


def main(port):
    bus = WaveshareAdapter(port)
    bus.listen(on_msg)
    print(f"Sending CAN heartbeat and listening started on {port}. Press Ctrl+C to stop.")

    try:
        while True:
            bus.send(0x123, [0xAA, 0xBB])
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        bus.close()


if __name__ == "__main__":

    # NOTE change default port to match your machine or provide it with --port
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=str, default="/dev/ttys008")
    port = parser.parse_args().port

    main(port)
    