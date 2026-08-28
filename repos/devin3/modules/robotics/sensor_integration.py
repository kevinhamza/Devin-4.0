# # Devin/modules/robotics/sensor_integration.py
# # Purpose: Provides a framework for integrating with and reading data from
# #          various robot sensors like cameras, IMUs, and LiDAR.

# import logging
# import time
# import random
# from abc import ABC, abstractmethod
# from enum import Enum
# from dataclasses import dataclass
# from typing import Optional, Any, Dict, List, Tuple

# # --- Important Libraries for a Real Implementation ---
# # This module would rely on libraries for specific sensor types.
# #
# # import cv2 # OpenCV for camera interactions
# # import numpy as np # For handling image data, point clouds, etc.
# # import serial # For sensors that communicate over a serial port

# # Configure basic logging
# logger = logging.getLogger("SensorIntegration")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# class SensorType(Enum):
#     """Enumeration for different types of robot sensors."""
#     CAMERA = "Camera"
#     IMU = "Inertial Measurement Unit"
#     LIDAR = "Light Detection and Ranging"
#     FORCE_TORQUE = "Force-Torque Sensor"

# class Sensor(ABC):
#     """An abstract base class that defines the contract for any sensor."""
#     def __init__(self, sensor_id: str, sensor_type: SensorType):
#         self.sensor_id = sensor_id
#         self.sensor_type = sensor_type
#         self.is_active = False
#         logger.info(f"Sensor '{self.sensor_id}' ({self.sensor_type.value}) initialized.")

#     @abstractmethod
#     def connect(self) -> bool:
#         """Establishes a connection to the sensor hardware."""
#         pass

#     @abstractmethod
#     def read_data(self) -> Any:
#         """Reads and returns the latest data from the sensor."""
#         pass

#     def get_status(self) -> Dict[str, Any]:
#         """Returns the current status of the sensor."""
#         return {"sensor_id": self.sensor_id, "type": self.sensor_type.value, "is_active": self.is_active}

# # --- Concrete Sensor Implementations ---

# class Camera(Sensor):
#     """Conceptual implementation for a camera sensor."""
#     def __init__(self, sensor_id: str, device_index: int = 0, resolution: Tuple[int, int] = (1280, 720)):
#         super().__init__(sensor_id, SensorType.CAMERA)
#         self.device_index = device_index
#         self.resolution = resolution
#         self.camera_capture_conceptual: Optional[Any] = None

#     def connect(self) -> bool:
#         logger.info(f"CONCEPTUAL OPENCV: Connecting to camera at index {self.device_index}...")
#         # Real-world: self.capture = cv2.VideoCapture(self.device_index)
#         # if not self.capture.isOpened(): self.is_active = False; return False
#         self.camera_capture_conceptual = f"<Conceptual cv2.VideoCapture object for device {self.device_index}>"
#         self.is_active = True
#         return True

#     def read_data(self) -> Any:
#         """Conceptually captures and returns an image frame."""
#         if not self.is_active: return None
#         logger.info(f"CONCEPTUAL OPENCV: Reading frame from camera '{self.sensor_id}'.")
#         # Real-world: ret, frame = self.capture.read()
#         # if ret: return frame
#         # We'll return a conceptual numpy array.
#         return f"<Conceptual NumPy array: shape={self.resolution}, dtype=uint8>"

# class IMU(Sensor):
#     """Conceptual implementation for an Inertial Measurement Unit."""
#     def __init__(self, sensor_id: str, port: str):
#         super().__init__(sensor_id, SensorType.IMU)
#         self.port = port # e.g., a serial port

#     def connect(self) -> bool:
#         logger.info(f"CONCEPTUAL SERIAL: Connecting to IMU on port {self.port}...")
#         self.is_active = True
#         return True

#     def read_data(self) -> Dict[str, Dict[str, float]]:
#         """Conceptually reads orientation and acceleration data."""
#         if not self.is_active: return {}
#         logger.info(f"CONCEPTUAL: Reading data packet from IMU '{self.sensor_id}'.")
#         return {
#             "orientation_quaternion": {
#                 "w": round(random.uniform(0, 1), 4),
#                 "x": round(random.uniform(-1, 1), 4),
#                 "y": round(random.uniform(-1, 1), 4),
#                 "z": round(random.uniform(-1, 1), 4),
#             },
#             "linear_acceleration_ms2": {
#                 "x": round(random.uniform(-0.1, 0.1), 4),
#                 "y": round(random.uniform(-0.1, 0.1), 4),
#                 "z": round(random.uniform(9.7, 9.9), 4),
#             }
#         }

# class Lidar(Sensor):
#     """Conceptual implementation for a 2D LiDAR scanner."""
#     def __init__(self, sensor_id: str):
#         super().__init__(sensor_id, SensorType.LIDAR)
    
#     def connect(self) -> bool:
#         logger.info(f"CONCEPTUAL: Connecting to LiDAR sensor '{self.sensor_id}'...")
#         self.is_active = True
#         return True

#     def read_data(self) -> List[Tuple[float, float]]:
#         """Conceptually returns a 360-degree laser scan."""
#         if not self.is_active: return []
#         logger.info(f"CONCEPTUAL: Reading 360-degree scan from LiDAR '{self.sensor_id}'.")
#         # Data is a list of (angle_degrees, distance_meters) tuples.
#         scan_data = []
#         for angle in range(0, 360, 5): # A point every 5 degrees
#             distance = round(random.uniform(0.5, 10.0), 3)
#             scan_data.append((float(angle), distance))
#         return scan_data

# # --- Sensor Management ---

# class SensorSuite:
#     """Manages all the sensors attached to the robot."""
#     def __init__(self):
#         self.sensors: Dict[str, Sensor] = {}
#         logger.info("SensorSuite initialized.")

#     def add_sensor(self, sensor: Sensor) -> bool:
#         """Adds and connects a new sensor to the suite."""
#         logger.info(f"Adding sensor '{sensor.sensor_id}' to the suite...")
#         if sensor.connect():
#             self.sensors[sensor.sensor_id] = sensor
#             logger.info(f"  Sensor '{sensor.sensor_id}' added and connected successfully.")
#             return True
#         else:
#             logger.error(f"  Failed to connect sensor '{sensor.sensor_id}'. Not added.")
#             return False

#     def get_all_sensor_data(self) -> Dict[str, Any]:
#         """Polls all active sensors and returns a dictionary of their data."""
#         logger.info("Polling all sensors for data...")
#         all_data = {}
#         for sensor_id, sensor in self.sensors.items():
#             if sensor.is_active:
#                 all_data[sensor_id] = sensor.read_data()
#         return all_data

# # --- Example Usage ---
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== Sensor Integration Prototype 👁️ ===")
#     print("=========================================================")

#     # 1. Initialize the main sensor management suite
#     robot_sensors = SensorSuite()

#     # 2. Create and add specific sensors
#     print("\n--- Initializing and adding sensors ---")
    
#     # Add a camera on the robot's wrist
#     wrist_cam = Camera(sensor_id="wrist_camera", device_index=0)
#     robot_sensors.add_sensor(wrist_cam)
    
#     # Add an IMU in the robot's base
#     base_imu = IMU(sensor_id="base_imu", port="/dev/ttyACM0")
#     robot_sensors.add_sensor(base_imu)
    
#     # Add a LiDAR scanner for navigation
#     lidar_scanner = Lidar(sensor_id="lidar_2d")
#     robot_sensors.add_sensor(lidar_scanner)

#     print(f"\n{len(robot_sensors.sensors)} sensors are now active.")

#     # 3. Get a complete snapshot of the robot's perception
#     print("\n\n--- Getting a full sensor data snapshot ---")
#     sensor_snapshot = robot_sensors.get_all_sensor_data()

#     for sensor_id, data in sensor_snapshot.items():
#         print(f"\n  Data from '{sensor_id}':")
#         if isinstance(data, dict): # IMU data
#             print(f"    - Orientation (w): {data.get('orientation_quaternion', {}).get('w')}")
#             print(f"    - Z-axis Acceleration: {data.get('linear_acceleration_ms2', {}).get('z')}")
#         elif isinstance(data, list): # LiDAR data
#             print(f"    - Got {len(data)} laser scan points. First point: Angle={data[0][0]}°, Dist={data[0][1]}m")
#         else: # Camera data
#             print(f"    - {data}")

#     # 4. Use a specific sensor's method
#     print("\n\n--- Performing a specific sensor action ---")
#     print("  Capturing a high-resolution image from the wrist camera...")
#     image_frame = wrist_cam.read_data()
#     print(f"  Image captured: {image_frame}")
#     # In a real system: cv2.imwrite('capture.jpg', image_frame)


#     print("\n=========================================================")
#     print("=== Sensor Integration Prototype Complete ===")
#     print("=========================================================")


# Devin/modules/robotics/sensor_integration.py
# Purpose: A functional framework for integrating with and reading data from
#          various robot sensors like cameras, IMUs, and LiDAR.

import logging
import time
import platform
import threading
import shlex
import subprocess
import yaml
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Any, Dict, List, Tuple

try:
    import cv2
    import numpy as np
    import serial
    CV2_NUMPY_SERIAL_AVAILABLE = True
except ImportError as e:
    CV2_NUMPY_SERIAL_AVAILABLE = False
    _import_error = e

# Configure basic logging
logger = logging.getLogger("SensorIntegration")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)

class SensorType(Enum):
    CAMERA = "Camera"
    IMU = "Inertial Measurement Unit"
    LIDAR = "Light Detection and Ranging"

class Sensor(ABC):
    """Abstract base class that defines the contract for any sensor."""
    def __init__(self, sensor_id: str, sensor_type: SensorType):
        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self.is_active = False

    @abstractmethod
    def connect(self) -> bool: pass
    @abstractmethod
    def read_data(self) -> Any: pass

class Camera(Sensor):
    """Implementation for a camera sensor using OpenCV."""
    def __init__(self, sensor_id: str, device_index: int = 0):
        super().__init__(sensor_id, SensorType.CAMERA)
        self.device_index = device_index
        self.capture: Optional[cv2.VideoCapture] = None

    def connect(self) -> bool:
        logger.info(f"Connecting to camera at index {self.device_index}...")
        self.capture = cv2.VideoCapture(self.device_index)
        if not self.capture.isOpened():
            logger.error(f"Failed to open camera at index {self.device_index}.")
            self.is_active = False
            return False
        self.is_active = True
        return True

    def read_data(self) -> Optional[np.ndarray]:
        """Captures and returns an image frame as a NumPy array."""
        if not self.is_active or not self.capture: return None
        ret, frame = self.capture.read()
        return frame if ret else None

    def disconnect(self):
        if self.capture: self.capture.release()
        self.is_active = False

class IMU(Sensor):
    """Implementation for an IMU sensor communicating over a serial port."""
    def __init__(self, sensor_id: str, port: str, baudrate: int = 9600):
        super().__init__(sensor_id, SensorType.IMU)
        self.port_name = port
        self.baudrate = baudrate
        self.serial_conn: Optional[serial.Serial] = None

    def connect(self) -> bool:
        try:
            self.serial_conn = serial.Serial(self.port_name, self.baudrate, timeout=1)
            self.is_active = True
            return True
        except serial.SerialException as e:
            logger.error(f"Failed to connect to IMU on port '{self.port_name}': {e}")
            return False

    def read_data(self) -> Optional[Dict[str, float]]:
        """Reads and parses a line of comma-separated data from the serial port."""
        if not self.is_active or not self.serial_conn: return None
        try:
            line = self.serial_conn.readline().decode('utf-8').strip()
            if not line: return None
            # Expecting a simple format like: ax,ay,az,gx,gy,gz
            parts = [float(p) for p in line.split(',')]
            if len(parts) == 6:
                return {"ax": parts[0], "ay": parts[1], "az": parts[2], "gx": parts[3], "gy": parts[4], "gz": parts[5]}
        except (ValueError, IndexError, UnicodeDecodeError) as e:
            logger.warning(f"Could not parse IMU data line: {e}")
        return None

class Lidar(Sensor):
    """Implementation for a LiDAR scanner that publishes to a ROS 2 topic."""
    def __init__(self, sensor_id: str, topic_name: str = "/scan"):
        super().__init__(sensor_id, SensorType.LIDAR)
        self.topic_name = topic_name

    def connect(self) -> bool:
        # For ROS, "connecting" means verifying the ROS environment is active
        if shutil.which("ros2"):
            self.is_active = True
            return True
        logger.error("ROS 2 environment not detected (`ros2` command not found).")
        return False

    def read_data(self) -> Optional[Dict]:
        """Captures a single message from a ROS 2 LaserScan topic."""
        if not self.is_active: return None
        command = f"ros2 topic echo {self.topic_name} --once --no-arr"
        try:
            # We use a timeout in case the topic isn't publishing
            result = subprocess.run(shlex.split(command), capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout:
                # The output is YAML, so we can parse it
                return yaml.safe_load(result.stdout.split('---')[0]) # Get first message
        except subprocess.TimeoutExpired:
            logger.error(f"Timed out waiting for message on ROS 2 topic '{self.topic_name}'.")
        except Exception as e:
            logger.error(f"Failed to read from ROS 2 topic: {e}")
        return None

class SensorSuite:
    """Manages all the sensors attached to the robot."""
    def __init__(self):
        self.sensors: Dict[str, Sensor] = {}

    def add_sensor(self, sensor: Sensor):
        if sensor.connect():
            self.sensors[sensor.sensor_id] = sensor
        else:
            logger.error(f"Failed to connect and add sensor '{sensor.sensor_id}'.")

    def get_all_sensor_data(self) -> Dict[str, Any]:
        """Polls all active sensors and returns their data."""
        return {sid: s.read_data() for sid, s in self.sensors.items()}

# --- Example Usage ---
def mock_imu_server(port_name: str, stop_event: threading.Event):
    """A mock server that writes IMU-like data to a serial port."""
    try:
        with serial.Serial(port_name, 9600) as ser:
            logger.info(f"[Mock IMU] Writing data to {port_name}...")
            while not stop_event.is_set():
                # ax, ay, az, gx, gy, gz
                data_line = f"{time.time()%2-1:.3f},{time.time()%3-1.5:.3f},9.81,{time.time()%0.5:.3f},{time.time()%0.3:.3f},{time.time()%0.4:.3f}\n"
                ser.write(data_line.encode('utf-8'))
                time.sleep(0.1)
    except serial.SerialException as e:
        logger.error(f"[Mock IMU] Error: {e}")

if __name__ == "__main__":
    import shutil
    print("=========================================================")
    print("=== Integrated Sensor Integration Demo 👁️ ===")
    print("=========================================================")

    if not CV2_NUMPY_SERIAL_AVAILABLE:
        print(f"\nERROR: A core dependency is missing. Error: {_import_error}")
    else:
        # --- 1. Camera Demo ---
        print("\n--- 1. Testing Camera Sensor ---")
        wrist_cam = Camera(sensor_id="system_webcam")
        if wrist_cam.connect():
            frame = wrist_cam.read_data()
            if frame is not None:
                filepath = "live_camera_capture.jpg"
                cv2.imwrite(filepath, frame)
                print(f"  [SUCCESS] Live frame captured from webcam and saved to '{filepath}'")
            else:
                print("  [FAILURE] Could not read frame from webcam.")
            wrist_cam.disconnect()
        else:
            print("  [SKIPPED] No camera found or could not connect.")

        # --- 2. IMU Demo (with serial loopback) ---
        print("\n\n--- 2. Testing IMU Sensor (with virtual serial port) ---")
        if platform.system() == "Linux" and shutil.which("socat"):
            port1, port2 = "./ttydevin_imu0", "./ttydevin_imu1"
            socat_proc = subprocess.Popen(shlex.split(f"socat -d -d pty,raw,echo=0,link={port1} pty,raw,echo=0,link={port2}"))
            time.sleep(1)

            stop_event = threading.Event()
            imu_server_thread = threading.Thread(target=mock_imu_server, args=(port2, stop_event))
            imu_server_thread.start()
            
            base_imu = IMU(sensor_id="mock_imu", port=port1)
            if base_imu.connect():
                print("  Reading 5 data points from mock IMU...")
                for i in range(5):
                    data = base_imu.read_data()
                    print(f"    - Read {i+1}: {data}")
                    time.sleep(0.1)
                
            stop_event.set()
            imu_server_thread.join()
            socat_proc.terminate()
            if os.path.exists(port1): os.remove(port1)
            if os.path.exists(port2): os.remove(port2)
        else:
            print("  [SKIPPED] IMU loopback demo requires `socat` on Linux.")
            
        # --- 3. LiDAR Demo (informational) ---
        print("\n\n--- 3. Testing LiDAR Sensor (Informational) ---")
        if shutil.which("ros2"):
            print("  `ros2` command found. The Lidar class is available.")
            print("  To test it, you would need a running ROS 2 system with a LiDAR")
            print("  publishing to the '/scan' topic. The class would run:")
            print("    ros2 topic echo /scan --once --no-arr")
        else:
            print("  [SKIPPED] `ros2` command not found. LiDAR functionality unavailable.")

    print("\n=========================================================")
    print("=== Sensor Integration Demo Complete ===")
    print("=========================================================")
