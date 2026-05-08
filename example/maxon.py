import time
from crater_can import OpMode, EPOS4


def main():
    PORT = '/dev/cu.usbserial-140'
    NODE = 1
    
    # 1. Initialize our controller
    drive = EPOS4(port=PORT, node_id=NODE)
    
    try:
        # Start the node broadcasting
        drive.nmt_start()
        time.sleep(0.1)

        # 2. Safe Startup Routine
        drive.reset_fault()
        drive.set_mode(OpMode.PROFILE_VELOCITY)
        drive.enable()

        # 3. Motion Test
        drive.set_velocity(500)  # Spin at 500 RPM
        
        # Let it spin for 5 seconds, printing the statusword
        print("\n--- Running (Press Ctrl+C to stop) ---")
        for _ in range(5):
            print(f"Statusword: {hex(drive.statusword)}")
            time.sleep(1)
            
        # 4. Stop Motor
        drive.set_velocity(0)
        time.sleep(1) # wait for it to spin down
        drive.disable()

    except KeyboardInterrupt:
        print("\n[USER] Interrupted by user. Emergency Stop.")
        drive.set_velocity(0)
        drive.disable()
        
    finally:
        # 5. Always clean up the adapter so it doesn't lock up next run
        drive.stop_bus()

if __name__ == "__main__":
    main()