import time
import struct
import threading
import tkinter as tk
from typing import List, Dict, Optional
from .waveshare_adapter import CANFrame
from .epos4_constants import (
    ObjectIndex, SDOCommand, StatusBit, ControlCommand, OpMode, CANopenID
)
import serial
import math


# NOTE VIBE CODED THE FUCK OUT OF IT
# NO IDEA HOW IT WORKS


class EPOS4Simulator:
    def __init__(self, node_id: int):
        self.node_id = node_id
        self.sdo_rx_id = CANopenID.SDO_TX_BASE + node_id # Simulator receives what PC sends
        self.sdo_tx_id = CANopenID.SDO_RX_BASE + node_id # Simulator sends what PC receives
        
        # Internal State
        self.statusword = StatusBit.SWITCH_ON_DISABLED
        self.op_mode = OpMode.PROFILE_VELOCITY
        self.position = 0.0
        self.velocity = 0  # RPM
        self.target_position = 0
        
        self.logs: List[str] = []
        self._last_time = time.time()
        self._last_heartbeat_time = 0.0
        
        # Position Mode specific
        self.is_moving_to_pos = False
        self._last_controlword = 0x0000

    def log(self, message: str):
        t = time.strftime("%H:%M:%S")
        self.logs.append(f"[{t}] {message}")

    def update_physics(self):
        now = time.time()
        dt = now - self._last_time
        self._last_time = now

        if not (self.statusword & StatusBit.OPERATION_ENABLED):
            return

        if self.op_mode == OpMode.PROFILE_VELOCITY:
            self.position += (self.velocity / 60.0) * 10000 * dt
            # Clear Target Reached in velocity mode usually
            self.statusword &= ~StatusBit.TARGET_REACHED 

        elif self.op_mode == OpMode.PROFILE_POSITION:
            if self.is_moving_to_pos:
                diff = self.target_position - self.position
                step = 15000 * dt  # Virtual "Speed" for position moves
                
                if abs(diff) < step:
                    self.position = self.target_position
                    self.is_moving_to_pos = False
                    self.statusword |= StatusBit.TARGET_REACHED
                    self.log("Target Reached.")
                else:
                    self.statusword &= ~StatusBit.TARGET_REACHED
                    if diff > 0:
                        self.position += step
                    else:
                        self.position -= step

    def _update_state_machine(self, ctrl: int):
        # Check for transitions
        # Bit 4 is "New Set-point" (0x0010)
        new_setpoint_bit = (ctrl & 0x0010)
        last_setpoint_bit = (self._last_controlword & 0x0010)

        # Rising edge detection for position moves
        if self.op_mode == OpMode.PROFILE_POSITION:
            if new_setpoint_bit and not last_setpoint_bit:
                self.is_moving_to_pos = True
                self.statusword &= ~StatusBit.TARGET_REACHED
                self.log(f"New Set-point triggered: {int(self.target_position)}")

        # Standard State Transitions
        if ctrl == ControlCommand.SHUTDOWN:
            self.statusword = StatusBit.READY_TO_SWITCH_ON | StatusBit.VOLTAGE_ENABLED
        elif ctrl == ControlCommand.SWITCH_ON:
            self.statusword = StatusBit.SWITCHED_ON | StatusBit.VOLTAGE_ENABLED
        elif ctrl == ControlCommand.ENABLE_OPERATION:
            self.statusword = StatusBit.OPERATION_ENABLED | StatusBit.VOLTAGE_ENABLED
        elif ctrl == ControlCommand.DISABLE_VOLTAGE:
            self.statusword = StatusBit.SWITCH_ON_DISABLED
            self.is_moving_to_pos = False

        self._last_controlword = ctrl
        
    def handle_sdo(self, data: bytes) -> Optional[bytes]:
        cmd = data[0]
        index = data[1] | (data[2] << 8)
        subindex = data[3]

        # --- SDO READ REQUESTS ---
        if cmd == SDOCommand.READ_REQUEST:
            res = bytearray([0x40, data[1], data[2], subindex, 0, 0, 0, 0])
            if index == ObjectIndex.STATUSWORD:
                res[0] = SDOCommand.READ_RES_2BYTE
                res[4:6] = struct.pack('<H', self.statusword)
            elif index == ObjectIndex.POSITION_ACTUAL:
                res[0] = SDOCommand.READ_RES_4BYTE
                res[4:8] = struct.pack('<i', int(self.position))
            elif index == ObjectIndex.VELOCITY_ACTUAL:
                res[0] = SDOCommand.READ_RES_4BYTE
                res[4:8] = struct.pack('<i', int(self.velocity))
            return bytes(res)

        # --- SDO WRITE REQUESTS ---
        elif cmd in [SDOCommand.WRITE_1BYTE, SDOCommand.WRITE_2BYTE, SDOCommand.WRITE_4BYTE]:
            val_bytes = data[4:8]
            
            if index == ObjectIndex.CONTROLWORD:
                ctrl = struct.unpack('<H', val_bytes[:2])[0]
                self._update_state_machine(ctrl)
            elif index == ObjectIndex.OP_MODE:
                self.op_mode = val_bytes[0]
                self.log(f"Mode changed to {OpMode(self.op_mode).name}")
            elif index == ObjectIndex.TARGET_VELOCITY:
                self.velocity = struct.unpack('<i', val_bytes)[0]
                self.log(f"Target Velocity: {self.velocity} RPM")
            elif index == ObjectIndex.TARGET_POSITION:
                move_val = struct.unpack('<i', val_bytes)[0]
                self.target_position = self.position + move_val
                self.log(f"Target Position (Rel): {move_val}")

            return bytes([SDOCommand.WRITE_SUCCESS, data[1], data[2], subindex, 0, 0, 0, 0])
        
        return None

    def should_send_heartbeat(self) -> bool:
        """Checks if 1 second has passed since the last beat."""
        now = time.time()
        if now - self._last_heartbeat_time > 1.0:
            self._last_heartbeat_time = now
            return True
        return False

    def get_heartbeat_data(self) -> bytes:
        """Returns the CANopen heartbeat payload (0x05 = Operational)."""
        return b'\x05'


class CraterSimulatorBus:

    def __init__(self, port: str, nodes: List[EPOS4Simulator]):
        # For virtual ports on macOS, we use 9600 or 0. 
        # The hardware-specific 'special baudrate' (2M) fails on PTYs.
        try:
            self.ser = serial.Serial(port, 2000000, timeout=0.01)
        except OSError:
            # Fallback for virtual ports (socat)
            print("Virtual port detected, bypassing high baudrate...")
            self.ser = serial.Serial(port, timeout=0.01) 
        
        self.nodes = {n.node_id: n for n in nodes}
        self.running = True

    def run_gui(self):
        root = tk.Tk()
        root.title("CraterCAN EPOS4 Simulator")
        
        canvases = {}
        log_boxes = {}

        for node_id, node in self.nodes.items():
            frame = tk.Frame(root, bd=2, relief=tk.SUNKEN)
            frame.pack(side=tk.LEFT, padx=10, pady=10)
            
            tk.Label(frame, text=f"Node ID: {node_id}", font=('Arial', 12, 'bold')).pack()
            
            c = tk.Canvas(frame, width=100, height=100, bg='white')
            c.pack()
            canvases[node_id] = c
            
            txt = tk.Text(frame, width=30, height=10, font=('Consolas', 8))
            txt.pack()
            log_boxes[node_id] = txt

        def update():
            # 1. Handle Physics & Heartbeats
            for nid, node in self.nodes.items():
                node.update_physics()
                
                if node.should_send_heartbeat():
                    # Heartbeat ID is 0x700 + NodeID
                    self._send_frame(0x700 + nid, node.get_heartbeat_data())

                # 2. Update Dial UI
                c = canvases[nid]
                c.delete("all")
                c.create_oval(10, 10, 90, 90, width=2)
                angle = (node.position % 10000) * (360/10000)
                rad = math.radians(angle - 90)
                x = 50 + 40 * math.cos(rad)
                y = 50 + 40 * math.sin(rad)
                c.create_line(50, 50, x, y, width=3, fill='red')
                
                # 3. Update Log UI
                while node.logs:
                    log_boxes[nid].insert(tk.END, node.logs.pop(0) + "\n")
                    log_boxes[nid].see(tk.END)

            # 4. Handle Incoming Serial Data (SDO Requests)
            if self.ser.in_waiting >= 20:
                header = self.ser.read(2)
                if header == b'\xAA\x55':
                    body = self.ser.read(18)
                    msg_id = struct.unpack('<I', body[3:7])[0]
                    # Extract Node ID from SDO (0x600 + NodeID)
                    target_node = msg_id - 0x600
                    if target_node in self.nodes:
                        response = self.nodes[target_node].handle_sdo(body[8:16])
                        if response:
                            self._send_frame(self.nodes[target_node].sdo_tx_id, response)
            
            root.after(20, update)

        update()
        root.mainloop()
        self.running = False

    def _send_frame(self, msg_id: int, data: bytes):
        frame = bytearray([0xAA, 0x55, 0x01, 0x01, 0x00])
        frame += struct.pack('<I', msg_id)
        frame.append(len(data))
        frame += data.ljust(8, b'\x00')
        frame.append(0x00)
        frame.append(sum(frame[2:]) & 0xFF)
        self.ser.write(frame)