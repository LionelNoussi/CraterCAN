import argparse

from crater_can.epos4_simulator import EPOS4Simulator, CraterSimulatorBus

# Run `socat -d -d pty,raw,echo=0 pty,raw,echo=0`
# to generate two virtual serial ports on your mac/linux machine

def main():
    parser = argparse.ArgumentParser(
        description="Run the EPOS4 simulator"
    )

    parser.add_argument(
        "--port",
        type=str,
        help="Serial port to bind the simulator to (e.g. /dev/ttys008)",
        default="/dev/ttys008"
    )

    args = parser.parse_args()

    sim_nodes = [
        EPOS4Simulator(node_id=1),
        EPOS4Simulator(node_id=2),
    ]

    bus_sim = CraterSimulatorBus(
        port=args.port,
        nodes=sim_nodes
    )

    print(
        "Simulator running... "
        "Connect your EPOS4Node to the paired COM port."
    )

    bus_sim.run_gui()


if __name__ == "__main__":
    main()