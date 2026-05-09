# Crater CAN

Internal repository for interfacing ESP32 micro-controllers and Maxon EPOS4 Motor Controllers with the Waveshare USB-CAN testbench adapter.

## Table of Contents

- [Python Setup](#python-setup)
- [Firmware Overview](#firmware-overview)
- [Maxon EPOS4 Physical Setup](#maxon-epos4-physical-setup)
- [Using the EPOS4 Simulator](#using-the-epos4-simulator)
- [Hardware Connections](#hardware-connections)
- [Example Usage](#example-usage)

---

# Python Setup Instructions

## 1. Create a Virtual Environment

```bash
[CraterCAN/] $ python -m venv .venv
```

## 2. Activate the Environment

- **Mac/Linux**
  ```bash
  source .venv/bin/activate
  ```

- **Windows**
  ```powershell
  .venv\Scripts\activate
  ```

## 3. Install the Package

Installs `crater_can` in editable mode for development.

```bash
[(.venv) CraterCAN/] $ pip install -e .
```

---

# Maxon EPOS4 Physical Setup

To interface with Maxon EPOS4 controllers, follow these hardware guidelines:

## 1. Wiring the Bus

The CAN bus must be a daisy-chain. Ensure the two ends of the physical bus are terminated with `120Ω` resistors.

## 2. Configuration (EPOS Studio)

Before using this library, connect to your controllers via USB using Maxon EPOS Studio and ensure:

- **Node ID:** Set each motor to a unique ID (e.g., `1`, `2`, `3`)
- **Automatic Bitrate Detection:** Usually enabled by default; the motor will "listen" to the bus to sync its speed

## 3. CANopen Objects

This library uses:

- **SDOs (Service Data Objects)** for synchronous configuration
- **Heartbeats** for connectivity monitoring

### Units

- **Position:** Measured in `"quadcounts"` (typically `10,000` steps per rotation)
- **Velocity:** Measured in `RPM`

---

# Using the EPOS4 Simulator

If you do not have physical hardware, you can develop using the built-in simulator and a virtual serial bridge.

## 1. Setup Virtual Ports (macOS)

Install `socat` and create a bridge:

```bash
brew install socat
socat -d -d pty,raw,echo=0 pty,raw,echo=0
```

This will output two ports, e.g.:

```text
/dev/ttys001
/dev/ttys002
```

## 2. Launch the Simulator

Run the simulator on one of the two ports in a separate terminal. This provides a GUI with virtual motor dials and real-time logs.

```bash
python example/simulate_canbus.py --port /dev/ttys002
```

## 3. Run the Control Logic

Run your script on the first port.

```bash
python example/maxon_example.py --port /dev/ttys001
```

The simulator mimics the **CiA 402 State Machine**:

```text
Shutdown -> Switch On -> Enable
```

The virtual motor will not move unless the proper enable sequence is followed.

---

# Firmware Overview

The `firmware` directory contains the C implementation for the ESP32 TWAI driver.

## Core Files

- `firmware/src/crater_can.c`
  - Hardware-specific TWAI implementation

- `firmware/include/crater_can.h`
  - Agnostic structures and error types

## Implementation Logic

### Init

`crater_can_init` installs the driver at `500 kbps`.

### Transmitting

Fill a `can_frame_t` and pass it to `crater_can_transmit`.

### Receiving

`crater_can_receive` blocks until a message arrives or a timeout occurs.

---

# Hardware Connections

## ESP32 to Transceiver

| MCU Pin | Transceiver Label |
|---|---|
| 5V | VCC |
| GND | GND |
| GPIO 4 | CAN TX |
| GPIO 5 | CAN RX |

## USB-CAN Adapter to EPOS4

| Adapter Label | EPOS4 CAN Header |
|---|---|
| CAN_H | CAN High |
| CAN_L | CAN Low |
| GND | Ground |

---

# Example Usage

The library is designed to be highly readable. All "Hex Magic" is hidden behind Enums.

```python
from crater_can import CraterCAN, EPOS4Node, OpMode

bus = CraterCAN(port='/dev/cu.usbserial-120')
bus.listen()

motor = EPOS4Node(bus, node_id=1)

if motor.wait_for_heartbeat():
    motor.clear_faults()
    motor.set_operation_mode(OpMode.PROFILE_VELOCITY)
    motor.enable()
    motor.set_velocity(500)  # 500 RPM
```

> **Note:** Always call `bus.stop()` at the end of your script to release the serial port.