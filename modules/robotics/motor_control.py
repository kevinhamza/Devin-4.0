# # Devin/modules/robotics/motor_control.py
# # Purpose: Provides a low-level interface for directly controlling and
# #          reading feedback from individual robot motors/servos.
# # (robotics # Robotics Logic (Very extensive, some duplication within))

# import logging
# import time
# import random
# from dataclasses import dataclass
# from typing import Optional, Any, Dict, List, Tuple

# # --- Important Libraries for a Real Implementation ---
# # This module would rely on libraries for hardware communication.
# #
# # import serial # For UART-based communication (common for Dynamixel, etc.)
# # import can # For CAN bus communication

# # Configure basic logging
# logger = logging.getLogger("MotorControl")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# @dataclass
# class MotorState:
#     """Holds the current state and feedback from a single motor."""
#     motor_id: int
#     present_position: int = 0  # Raw encoder value
#     present_speed: int = 0     # Raw speed value
#     present_load: float = 0.0  # Percentage of max torque
#     present_voltage: float = 12.0
#     present_temperature: int = 40 # Degrees Celsius
#     is_torque_enabled: bool = False
#     error_status: int = 0

# class MotorController:
#     """
#     A low-level controller that communicates directly with robot motors
#     over a conceptual communication bus (e.g., Serial/UART).
#     """
#     def __init__(self, port: str, baudrate: int = 1000000):
#         """
#         Initializes the controller and conceptually opens the communication port.

#         Args:
#             port (str): The serial port name (e.g., '/dev/ttyUSB0' on Linux, 'COM3' on Windows).
#             baudrate (int): The communication speed.
#         """
#         self.port = port
#         self.baudrate = baudrate
#         self.serial_connection_conceptual: Optional[Dict] = None
#         self.motor_states: Dict[int, MotorState] = {}
        
#         logger.info(f"MotorController initialized for port '{self.port}' at {self.baudrate} baud.")
#         self.connect_conceptual()

#     def connect_conceptual(self) -> bool:
#         """Conceptually opens the serial port."""
#         logger.info(f"CONCEPTUAL SERIAL: Opening port '{self.port}'...")
#         # Real-world: self.serial = serial.Serial(self.port, self.baudrate)
#         self.serial_connection_conceptual = {"status": "connected", "port": self.port}
#         return True

#     def disconnect_conceptual(self) -> None:
#         """Conceptually closes the serial port."""
#         if not self.serial_connection_conceptual: return
#         logger.info(f"CONCEPTUAL SERIAL: Closing port '{self.port}'.")
#         # Real-world: self.serial.close()
#         self.serial_connection_conceptual = None

#     def _send_packet_conceptual(self, packet: List[int]) -> bool:
#         """Conceptually sends a raw data packet to the bus."""
#         if not self.serial_connection_conceptual:
#             logger.error("Cannot send packet: Not connected.")
#             return False
#         hex_packet = ' '.join([f'0x{b:02X}' for b in packet])
#         logger.info(f"  BUS TX -> {hex_packet}")
#         # Real-world: self.serial.write(bytearray(packet))
#         return True

#     def discover_motors_conceptual(self, motor_ids: List[int]) -> int:
#         """
#         Conceptually pings a range of motor IDs to see which are on the bus.
#         """
#         logger.info(f"Pinging motor IDs {motor_ids}...")
#         found_count = 0
#         for motor_id in motor_ids:
#             # PING instruction packet for a Dynamixel motor (example)
#             ping_packet = [0xFF, 0xFF, motor_id, 0x02, 0x01, 255-motor_id-3]
#             self._send_packet_conceptual(ping_packet)
#             # In a real system, you'd wait for a response packet.
#             if random.random() > 0.1: # 90% chance of finding the motor
#                 logger.info(f"  -> Motor {motor_id} responded.")
#                 self.motor_states[motor_id] = MotorState(motor_id=motor_id)
#                 found_count += 1
#             else:
#                 logger.warning(f"  -> Motor {motor_id} did not respond.")
#         logger.info(f"Discovery complete. Found {found_count} motors.")
#         return found_count

#     def enable_motor_torque(self, motor_id: int, enable: bool) -> bool:
#         """Conceptually enables or disables torque for a specific motor."""
#         logger.info(f"Setting torque {'ENABLE' if enable else 'DISABLE'} for motor {motor_id}.")
#         # WRITE instruction for Torque Enable (address 24) on a Dynamixel
#         value = 1 if enable else 0
#         checksum = 255 - (motor_id + 4 + 3 + 24 + value) % 256
#         write_packet = [0xFF, 0xFF, motor_id, 0x04, 0x03, 24, value, checksum]
#         success = self._send_packet_conceptual(write_packet)
#         if success and motor_id in self.motor_states:
#             self.motor_states[motor_id].is_torque_enabled = enable
#         return success

#     def set_motor_goal_position(self, motor_id: int, position: int) -> bool:
#         """Conceptually sets the target position for a single motor."""
#         logger.info(f"Setting motor {motor_id} goal position to {position}.")
#         # WRITE instruction for Goal Position (address 30)
#         pos_lsb = position & 0xFF
#         pos_msb = position >> 8
#         checksum = 255 - (motor_id + 5 + 3 + 30 + pos_lsb + pos_msb) % 256
#         write_packet = [0xFF, 0xFF, motor_id, 0x05, 0x03, 30, pos_lsb, pos_msb, checksum]
#         return self._send_packet_conceptual(write_packet)

#     def sync_write_goal_positions(self, motor_goals: List[Tuple[int, int]]) -> bool:
#         """
#         Conceptually sends a single packet to command multiple motors simultaneously.
#         This is crucial for synchronized, smooth multi-joint movements.

#         Args:
#             motor_goals (List[Tuple[int, int]]): A list of (motor_id, position) tuples.
#         """
#         if not motor_goals: return False
#         logger.info(f"SYNC WRITE: Setting goal positions for {len(motor_goals)} motors.")
#         # SYNC_WRITE instruction (0x83) for Goal Position (address 30, length 2)
#         # Packet structure is complex: [header, id, length, instruction, start_addr, length_of_data, [id, data_lsb, data_msb], ..., checksum]
#         # This is a simplified conceptual representation.
#         sync_write_packet_header = [0xFF, 0xFF, 0xFE, 0, 0x83, 30, 2]
#         param_bytes = []
#         for motor_id, position in motor_goals:
#             pos_lsb = position & 0xFF
#             pos_msb = position >> 8
#             param_bytes.extend([motor_id, pos_lsb, pos_msb])
#             logger.info(f"  - Motor {motor_id} -> Position {position}")
        
#         # Calculate conceptual length and checksum
#         sync_write_packet_header[3] = len(param_bytes) + 4
#         # ... checksum calculation would go here ...
        
#         return self._send_packet_conceptual(sync_write_packet_header + param_bytes)

#     def get_motor_feedback(self, motor_id: int) -> Optional[MotorState]:
#         """Conceptually reads the current state (position, speed, etc.) from a motor."""
#         if motor_id not in self.motor_states: return None
#         logger.info(f"Requesting feedback from motor {motor_id}.")
#         # READ instruction packet would be sent here.
#         # Then we would wait for and parse the response packet.
        
#         # Simulate receiving new data
#         state = self.motor_states[motor_id]
#         state.present_position = random.randint(0, 4095)
#         state.present_speed = random.randint(0, 1023)
#         state.present_load = round(random.uniform(-50.0, 50.0), 2)
#         state.present_temperature = random.randint(35, 50)
        
#         logger.info(f"  BUS RX <- Feedback for motor {motor_id}: Pos={state.present_position}, Temp={state.present_temperature}°C")
#         return state

# # --- Example Usage ---
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== Low-Level Motor Controller Prototype 🦾 ===")
#     print("=========================================================")
    
#     # Initialize controller for a conceptual 6-DOF robot arm
#     robot_arm_controller = MotorController(port='/dev/ttyUSB0')
#     arm_motor_ids = [1, 2, 3, 4, 5, 6] # e.g., Base, Shoulder, Elbow, Wrist Roll/Pitch/Yaw

#     # --- 1. Discover and Initialize Motors ---
#     print("\n--- Step 1: Discovering and enabling motors ---")
#     robot_arm_controller.discover_motors_conceptual(arm_motor_ids)
    
#     for motor_id in arm_motor_ids:
#         robot_arm_controller.enable_motor_torque(motor_id, enable=True)
    
#     # --- 2. Move to a "Home" Position using SYNC_WRITE ---
#     # Positions are raw encoder values (e.g., 0-4095 for many servos)
#     home_position_goals = [
#         (1, 2048), # Base to center
#         (2, 2048), # Shoulder to center
#         (3, 1024), # Elbow bent
#         (4, 2048), # Wrist roll center
#         (5, 1536), # Wrist pitch
#         (6, 2048)  # Wrist yaw center
#     ]
#     print("\n\n--- Step 2: Moving arm to 'Home' position using a single synchronized command ---")
#     robot_arm_controller.sync_write_goal_positions(home_position_goals)
    
#     # Simulate waiting for the move to complete
#     print("\n  (Simulating wait for 2 seconds for move to complete...)")
#     time.sleep(2)
    
#     # --- 3. Get Feedback from a specific motor ---
#     print("\n\n--- Step 3: Getting feedback from the elbow motor (ID 3) ---")
#     elbow_feedback = robot_arm_controller.get_motor_feedback(3)
#     if elbow_feedback:
#         print(f"  Elbow Motor Feedback:")
#         print(f"    - Position: {elbow_feedback.present_position}")
#         print(f"    - Speed: {elbow_feedback.present_speed}")
#         print(f"    - Load: {elbow_feedback.present_load}%")
#         print(f"    - Temperature: {elbow_feedback.present_temperature}°C")

#     # --- 4. Move to another position ---
#     gripper_open_position = [
#         (5, 2048), # Open gripper (controlled by wrist pitch motor for demo)
#     ]
#     print("\n\n--- Step 4: Sending a new command to open the gripper ---")
#     robot_arm_controller.sync_write_goal_positions(gripper_open_position)
    
#     # --- 5. Disconnect ---
#     print("\n\n--- Step 5: Disconnecting from motor bus ---")
#     robot_arm_controller.disconnect_conceptual()


#     print("\n=========================================================")
#     print("=== Motor Controller Prototype Complete ===")
#     print("=========================================================")


# Devin/modules/robotics/motor_control.py
# Purpose: A functional, low-level interface for controlling and reading
#          feedback from robot motors using the Dynamixel Protocol 1.0.

import logging
import time
import threading
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple
import os

try:
    import serial
    PYSERIAL_AVAILABLE = True
except ImportError:
    PYSERIAL_AVAILABLE = False

# Configure basic logging
logger = logging.getLogger("MotorControl")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False

@dataclass
class MotorState:
    motor_id: int
    present_position: int = 0
    is_torque_enabled: bool = False

class MotorController:
    """
    A low-level controller that communicates with Dynamixel-compatible motors
    over a serial bus using Protocol 1.0.
    """
    def __init__(self, port: str, baudrate: int = 1000000):
        if not PYSERIAL_AVAILABLE:
            raise ImportError("pyserial is required. 'pip install pyserial'")
        
        self.port_name = port
        self.baudrate = baudrate
        self.port: Optional[serial.Serial] = None
        self.connect()

    def connect(self):
        try:
            self.port = serial.Serial(self.port_name, self.baudrate, timeout=0.1)
            logger.info(f"Successfully opened serial port '{self.port_name}'.")
        except serial.SerialException as e:
            logger.error(f"Failed to open serial port '{self.port_name}': {e}")
            self.port = None

    def disconnect(self):
        if self.port and self.port.is_open:
            self.port.close()
            logger.info(f"Serial port '{self.port_name}' closed.")

    def _calculate_checksum(self, packet_data: List[int]) -> int:
        """Calculates the Dynamixel checksum."""
        return 255 - (sum(packet_data) % 256)

    def _send_and_receive(self, packet: List[int]) -> Optional[List[int]]:
        """Sends an instruction packet and waits for a status packet."""
        if not self.port: return None
        
        self.port.flushInput()
        self.port.write(bytearray(packet))
        
        # Wait for a response, which starts with 0xFF, 0xFF
        header = self.port.read(2)
        if header != b'\xff\xff':
            return None
        
        # Read the rest of the packet
        response_id_len = self.port.read(2)
        if not response_id_len: return None
        
        params_and_checksum = self.port.read(response_id_len[1])
        return list(header + response_id_len + params_and_checksum)

    def set_motor_goal_position(self, motor_id: int, position: int) -> bool:
        """Sets the target position for a single motor."""
        logger.info(f"Setting motor {motor_id} goal position to {position}.")
        # Dynamixel AX-12A Goal Position is at address 0x1E (30), length 2
        goal_pos_addr = 30
        pos_lsb = position & 0xFF
        pos_msb = position >> 8
        
        params = [motor_id, 5, 3, goal_pos_addr, pos_lsb, pos_msb]
        checksum = self._calculate_checksum(params)
        packet = [0xFF, 0xFF] + params + [checksum]
        
        response = self._send_and_receive(packet)
        return response is not None

    def get_motor_feedback(self, motor_id: int) -> Optional[MotorState]:
        """Reads the current state from a motor."""
        # Read 2 bytes starting from Present Position (address 36)
        read_addr = 36
        read_len = 2
        params = [motor_id, 4, 2, read_addr, read_len]
        checksum = self._calculate_checksum(params)
        packet = [0xFF, 0xFF] + params + [checksum]
        
        response = self._send_and_receive(packet)
        if response and len(response) >= 7:
            pos = response[5] + (response[6] << 8)
            return MotorState(motor_id=motor_id, present_position=pos)
        return None

# --- Example Usage with Serial Loopback Test ---
def mock_motor_server(port_name: str, stop_event: threading.Event):
    """A mock server that listens on a serial port and responds like a Dynamixel motor."""
    try:
        with serial.Serial(port_name, 1000000, timeout=1) as ser:
            logger.info(f"[Mock Motor] Listening on {port_name}...")
            while not stop_event.is_set():
                if ser.in_waiting >= 2:
                    header = ser.read(2)
                    if header == b'\xff\xff':
                        id_len_instr = ser.read(3)
                        params = ser.read(id_len_instr[1] - 1)
                        # Respond to a READ command for position
                        if id_len_instr[2] == 2: # READ instruction
                            response_params = [id_len_instr[0], 2, 0, 123, 4] # No error, pos=1147
                            checksum = 255 - (sum(response_params) % 256)
                            ser.write(bytearray([0xFF, 0xFF] + response_params + [checksum]))
    except serial.SerialException as e:
        logger.error(f"[Mock Motor] Error: {e}")
    logger.info("[Mock Motor] Shutting down.")

if __name__ == "__main__":
    import subprocess
    import platform
    
    print("=========================================================")
    print("=== Integrated Low-Level Motor Controller 🦾 ===")
    print("=========================================================")

    if not PYSERIAL_AVAILABLE:
        print("\nERROR: pyserial is required. 'pip install pyserial'")
    elif platform.system() != "Linux":
        print("\nNOTE: The automated loopback demo requires `socat` and is designed for Linux.")
        print("      You can still review the code, or test it with a physical serial loopback.")
    else:
        # --- 1. Setup a virtual serial port pair using socat ---
        print("\n--- 1. Setting up virtual serial port pair with `socat` ---")
        socat_proc = None
        port1, port2 = "./ttydevin0", "./ttydevin1"
        try:
            socat_cmd = f"socat -d -d pty,raw,echo=0,link={port1} pty,raw,echo=0,link={port2}"
            socat_proc = subprocess.Popen(shlex.split(socat_cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            time.sleep(1) # Give socat time to create the devices
            print(f"  Virtual ports created: {port1} <--> {port2}")

            # --- 2. Start the mock motor in a background thread ---
            stop_event = threading.Event()
            motor_thread = threading.Thread(target=mock_motor_server, args=(port2, stop_event))
            motor_thread.start()

            # --- 3. Initialize and use the real MotorController ---
            controller = MotorController(port=port1)
            if controller.port:
                # --- 4. Test communication ---
                print("\n--- 2. Testing communication with the mock motor ---")
                
                print("  > Setting goal position for motor 1...")
                success = controller.set_motor_goal_position(1, 1023)
                # We don't check the response for this simple mock, just that it doesn't fail
                print(f"  < Command sent successfully: {success}")
                
                print("\n  > Getting feedback from motor 1...")
                feedback = controller.get_motor_feedback(1)
                if feedback:
                    print(f"  < [SUCCESS] Received feedback: Position={feedback.present_position}")
                    assert feedback.present_position == 1147 # 123 + (4 << 8)
                else:
                    print("  < [FAILURE] Did not receive valid feedback.")
            
            # --- 5. Clean up ---
            print("\n--- 3. Shutting down ---")
            stop_event.set()
            motor_thread.join()
            controller.disconnect()

        except FileNotFoundError:
            print("\n[ERROR] `socat` command not found. Please install it to run the demo (`sudo apt-get install socat`).")
        except Exception as e:
            logger.error(f"An unexpected error occurred during the demo: {e}", exc_info=True)
        finally:
            if socat_proc:
                socat_proc.terminate()
            if os.path.exists(port1): os.remove(port1)
            if os.path.exists(port2): os.remove(port2)
    
    print("\n=========================================================")
    print("=== Motor Controller Prototype Complete ===")
    print("=========================================================")
