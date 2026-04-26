# Crater CAN

Internal repository for interfacing ESP32 micro-controllers with the Waveshare USB-CAN testbench adapter.

## Python Setup Instructions

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

## Firmware Overview

The firmware directory contains the C implementation for the ESP32. This code handles the low level TWAI driver configuration and message processing.

### Files in this directory

`firmware/src/crater_can.c`: Contains the hardware specific implementation for initialization, transmission, and reception.
`firmware/include/crater_can.h`: Defines the hardware agnostic can_frame_t structure and the crater_can_err_t error types
`example/main.c`: example application showing how to integrate these functions into a main execution loop.

### How to run the firmware

**Include the files:** Copy crater_can.h and crater_can.c into your project structure. If you are using ESP-IDF, ensure they are added to your CMakeLists.txt. If using PlatformIO or Arduino, place them in your src or lib folders.

**Configuration:** In your main file, define the GPIO pins used for TX and RX. For example, pins 4 and 5 are common for many microcontrollers.

**Initialization:** Call the `crater_can_init` function once at the start of your program. This function installs the TWAI driver at 500kbps and starts the CAN controller.

**Receiving Messages:** Use the `crater_can_receive` function to receive a `can_frame` with a specific timeout. Check the return error code, to see if a message was received, a timeout happened or the call failed for another reason. The result will be stored a the `can_frame` pointer, which was provided to the function.

**Transmitting Messages:** Use the `crater_can_transmit` function to transmit a message, by providing it a pointer to a properly filled out `can_frame`.

*Hardware Porting*
If you are using a non-ESP32 controller, you can keep the crater_can.h file to ensure your function signatures matches the rest of the team, but will have to re-implement the crater_can.c file for your hardware.


## Hardware Connections

Ensure the following 4-wire connection between the ESP32 and the testbench transceiver:

| MCU Pin | Transceiver Label |
|--------|------------------|
| 5V     | VCC              |
| GND    | GND              |
| GPIO 4 | CAN TX           |
| GPIO 5 | CAN RX           |

**Note:** Ensure the USB-CAN adapter is plugged into your computer before starting the Python script.



## Running the Example

### Important: Set your Serial Port

Before running the example, you must update the serial port string to match your machine's connection.

1. Open `example/main.py`
2. Find the line:
   ```python
   port = '/dev/cu.usbserial-120'
   ```
3. Change the string to your specific port e.g.:
   - Windows: `COM3`
   - Mac/Linux: `/dev/cu.usbserial-XXX`

### Flash your microcontroller

Copy the crater_can.h and crater_can.c files into your project and set-up a simple echo script, like in the example provided. Re-build your project and flash your micro-controller.

### Execute the Script

Run this command from the root directory:

```bash
[(.venv) CraterCAN/] $ python example/main.py
```




