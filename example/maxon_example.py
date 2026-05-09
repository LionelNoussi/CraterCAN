import time
from crater_can import CraterCAN, EPOS4Node, OpMode
import argparse


def main(port = "/dev/ttys009"):
    bus = CraterCAN(port=port, baud=2000000) 
    bus.listen()

    motor1 = EPOS4Node(bus, node_id=1, debug=True)
    motor2 = EPOS4Node(bus, node_id=2, debug=True)

    try:
        if not motor1.wait_for_heartbeat():
            print("Failed to connect to motor1. Check power and CAN bus.")
            return
        
        if not motor2.wait_for_heartbeat():
            print("Failed to connect to motor2. Check power and CAN bus.")
            return

        motor1.clear_faults()
        motor2.clear_faults()

        # Velocity Test
        print("\n--- Velocity Test ---")
        motor1.set_operation_mode(OpMode.PROFILE_VELOCITY)
        motor1.enable()

        motor2.set_operation_mode(OpMode.PROFILE_VELOCITY)
        motor2.enable()
        
        motor1.set_velocity(100)
        motor2.set_velocity(300)
        for _ in range(3):
            print(f"Current Speed 1: {motor1.get_actual_velocity()} RPM")
            print(f"Current Speed 2: {motor1.get_actual_velocity()} RPM")
            time.sleep(0.5)
            
        motor1.set_velocity(0)
        motor2.set_velocity(0)
        time.sleep(0.5)

        # Position Test
        print("\n--- Position Test ---")
        motor1.set_operation_mode(OpMode.PROFILE_POSITION)
        motor2.set_operation_mode(OpMode.PROFILE_POSITION)
        
        print("Moving motor1 10,000 steps forward...")
        motor1.move_position_relative(10000)

        print("Moving motor2 20,000 steps forward...")
        motor2.move_position_relative(20000)
        
        for _ in range(3):
            print(f"Current Position of Motor1: {motor1.get_actual_position()} steps")
            print(f"Current Position of Motor2: {motor2.get_actual_position()} steps")
            time.sleep(0.5)

    finally:
        motor1.disable()
        motor2.disable()
        bus.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run the EPOS4 simulator"
    )

    parser.add_argument(
        "--port",
        type=str,
        help="Serial port to bind the simulator to (e.g. /dev/ttys008)",
        default="/dev/ttys009"
    )

    args = parser.parse_args()
    main(args.port)