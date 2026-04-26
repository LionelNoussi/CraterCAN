import serial
import struct
import time

class WaveshareHardcodedCAN:
    def __init__(self, port, baudrate=2000000):
        # We use a 0.01 timeout for snappy response
        self.ser = serial.Serial(port, baudrate, timeout=0.01)
        self.ser.reset_input_buffer()
        print(f"Connected to {port}. Testing TX...")

    def send_can_frame(self, arb_id, data):
        """
        Constructs the exact 20-byte packet required by this firmware.
        """
        # 1. Header (2 bytes)
        frame = bytearray([0xAA, 0x55])
        
        # 2. Control Bytes (3 bytes)
        # Byte 2: 0x01 (Standard CAN)
        # Byte 3: 0x01 (Data Frame)
        # Byte 4: 0x00 (COMMAND: SEND) <- This is likely why it was failing
        frame += bytearray([0x01, 0x01, 0x00])
        
        # 3. ID (4 bytes, Little Endian)
        # Based on your RX log: 20 00 00 00
        frame += struct.pack('<I', arb_id)
        
        # 4. DLC (1 byte)
        dlc = len(data)
        frame.append(dlc)
        
        # 5. Data (8 bytes, must be padded)
        payload = bytes(data).ljust(8, b'\x00')
        frame += payload
        
        # 6. Reserved/Padding (1 byte)
        # Your RX log showed 0x00 here
        frame.append(0x00)
        
        # 7. Checksum (1 byte)
        # Sum of bytes index 2 through 18
        chk = sum(frame[2:]) & 0xFF
        frame.append(chk)
        
        # FINAL CHECK: Frame must be exactly 20 bytes
        if len(frame) != 20:
            print(f"Error: Frame length is {len(frame)}, should be 20")
            return

        self.ser.write(frame)
        self.ser.flush()

    def receive_and_print(self):
        # Efficiently look for the AA 55 header
        if self.ser.in_waiting >= 20:
            raw = self.ser.read(1)
            if raw == b'\xAA':
                if self.ser.read(1) == b'\x55':
                    body = self.ser.read(18)
                    if len(body) < 18: return
                    
                    # Based on your log, ID is at body[3:7]
                    # Data is at body[8:8+DLC]
                    arb_id = struct.unpack('<I', body[3:7])[0]
                    dlc = body[7]
                    data = body[8:8+dlc]
                    print(f"RECV: ID={hex(arb_id)} Data={data.hex(' ')}")

# --- TEST EXECUTION ---
adapter = WaveshareHardcodedCAN('/dev/cu.usbserial-120')

try:
    print("Sending ID 0x123 to ESP32... Watch for the TX light!")
    while True:
        # We send ID 0x123 (which is 291 decimal)
        # Sending 4 bytes: [10, 20, 30, 40]
        adapter.send_can_frame(0x123, [0x0A, 0x0B, 0x0C, 0x0D])
        
        # Listen for the ESP32 heartbeat (0x20)
        for _ in range(10):
            adapter.receive_and_print()
            time.sleep(0.05)

except KeyboardInterrupt:
    print("\nStopping...")
finally:
    adapter.ser.close()