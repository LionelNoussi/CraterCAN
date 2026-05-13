import time
from crater_can import WaveshareAdapter, EPOS4Node, OpMode
import argparse


def main(port):
    bus = WaveshareAdapter(port=port, baud=2000000) 
    bus.listen()

    node_ids = [1, 2, 3, 4]
    motors: list[EPOS4Node] = [
        EPOS4Node(bus, node_id=node_id, debug=True) for node_id in node_ids
    ]

    try:
        for motor in motors:
            if not motor.wait_for_heartbeat():
                print(f"Failed to connect to motor {motor.node_id}. Check power and CAN bus.")
                return

        for motor in motors:
            motor.clear_faults()
            motor.enable()
            
        print("\n--- Position Test ---")
        for motor in motors:
            print(f"Moving motor {motor.node_id} 10,000 steps forward...")
            motor.set_operation_mode(OpMode.PROFILE_POSITION)
            motor.move_position_relative(10000)

        time.sleep(10)
            
    finally:
        for motor in motors:
            motor.disable()
        bus.close()


if __name__ == "__main__":

    # NOTE change default port to match your machine or provide it with --port
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=str, default="/dev/ttys008")
    port = parser.parse_args().port
    
    main(port)