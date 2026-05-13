import argparse
from crater_can.epos4_simulator import EPOS4Simulator, CraterSimulatorBus


# NOTE
# Run `socat -d -d pty,raw,echo=0 pty,raw,echo=0`
# to generate two virtual serial ports on your mac/linux machine


def main(port):

    sim_nodes = [
        EPOS4Simulator(node_id=node_id)
        for node_id in [1, 2, 3, 4]
    ]

    bus_sim = CraterSimulatorBus(
        port=port,
        nodes=sim_nodes
    )

    print(
        "Simulator running... "
        "Connect your EPOS4Node to the paired COM port."
    )

    bus_sim.run_gui()


if __name__ == "__main__":

    # NOTE change default port to match your machine or provide it with --port
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=str, default="/dev/ttys008")
    port = parser.parse_args().port
    
    main(port)