# Crater CAN Bridge

Internal repository for interfacing ESP32 micro-controllers with the Waveshare USB-CAN testbench adapter.

## Setup Instructions

### 1. Create a Virtual Environment
Run this command from the root of the repository:

```bash
[CraterCAN/] $ python -m venv .venv
```

### 2. Activate the Environment

**Mac/Linux:**
```bash
[CraterCAN/] $ source .venv/bin/activate
```

**Windows:**
```bash
[CraterCAN/] $ .venv\Scripts\activate
```

### 3. Install the Package

This installs the `crater_can` library in editable mode. This means any changes you make to the source code apply immediately without needing to reinstall.

```bash
[(.venv) CraterCAN/] $ pip install -e .
```

## Running the Example

### Important: Set your Serial Port

Before running the example, you must update the serial port string to match your machine's connection.

1. Open `example/basic_test.py`
2. Find the line:
   ```python
   port = '/dev/cu.usbserial-120'
   ```
3. Change the string to your specific port e.g.:
   - Windows: `COM3`
   - Mac/Linux: `/dev/cu.usbserial-XXX`

### Execute the Script

Run this command from the root directory:

```bash
[(.venv) CraterCAN/] $ python example/basic_test.py
```

## Hardware Connections

Ensure the following 4-wire connection between the ESP32 and the testbench transceiver:

| MCU Pin | Transceiver Label |
|--------|------------------|
| 5V     | VCC              |
| GND    | GND              |
| GPIO 4 | CAN TX           |
| GPIO 5 | CAN RX           |

**Note:** Ensure the USB-CAN adapter is plugged into your computer before starting the Python script.
