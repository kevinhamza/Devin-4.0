# # Devin/modules/robotics/diagnostic_tools.py
# # Purpose: Provides a suite of tools for running diagnostics on all robotics
# #          components, from hardware connectivity to software module status.

# import logging
# import threading
# import time
# from datetime import datetime
# from enum import Enum, auto
# from typing import Dict, Any, Optional

# # This module would import all other robotics modules to check them.
# # from .motor_control import MotorController
# # from .sensor_integration import SensorSuite
# # from .ai_navigation import AINavigationSystem, NavigationStatus
# # ...and so on.

# # --- Conceptual Placeholders for Imported Modules ---
# class MockMotorController:
#     def check_motor_connectivity(self, motor_ids):
#         # Simulate one motor failing to respond
#         responsive = {mid: (True if mid != 3 else False) for mid in motor_ids}
#         return responsive
#     def get_motor_feedback(self, motor_id):
#         # Simulate one motor overheating
#         temp = 85 if motor_id == 4 else 45
#         return {"temperature": temp, "voltage": 12.1}

# class MockSensorSuite:
#     def get_all_statuses(self):
#         # Simulate one sensor being inactive
#         return {
#             "wrist_camera": {"is_active": True},
#             "base_imu": {"is_active": True},
#             "lidar_2d": {"is_active": False}
#         }

# class MockAINavigationSystem:
#     def get_status(self):
#         return {"status": "IDLE"}

# # --- End of Conceptual Placeholders ---

# # Configure basic logging
# logger = logging.getLogger("RoboticsDiagnostics")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# class HealthStatus(Enum):
#     OK = "OK"
#     WARNING = "WARNING"
#     ERROR = "ERROR"
#     UNKNOWN = "UNKNOWN"

# class RoboticsDiagnostics:
#     """
#     Aggregates status and runs health checks on all robotics components.
#     """
#     def __init__(self, **kwargs):
#         """
#         Initializes the diagnostics tool with all robotics modules.

#         Args:
#             **kwargs: Pass in all robotics modules, e.g.,
#                       motor_controller=my_motor_controller,
#                       sensor_suite=my_sensor_suite
#         """
#         self.motor_controller = kwargs.get("motor_controller")
#         self.sensor_suite = kwargs.get("sensor_suite")
#         self.navigation_system = kwargs.get("navigation_system")
#         self.all_motor_ids = kwargs.get("motor_ids", [])
        
#         self.monitoring_thread: Optional[threading.Thread] = None
#         self._stop_event = threading.Event()
        
#         logger.info("Robotics Diagnostics tool initialized.")

#     def _check_motor_controller(self) -> Dict[str, Any]:
#         """Runs diagnostics on the motor controller and individual motors."""
#         if not self.motor_controller:
#             return {"status": HealthStatus.UNKNOWN.name, "details": "Module not provided."}
        
#         report = {"status": HealthStatus.OK.name, "details": {}}
#         warnings, errors = [], []

#         # 1. Check motor connectivity
#         connectivity = self.motor_controller.check_motor_connectivity(self.all_motor_ids)
#         responsive_motors = [mid for mid, status in connectivity.items() if status]
#         unresponsive_motors = [mid for mid, status in connectivity.items() if not status]
#         report["details"]["connectivity"] = f"{len(responsive_motors)}/{len(self.all_motor_ids)} motors responding."
#         if unresponsive_motors:
#             errors.append(f"Motors not responding: {unresponsive_motors}")

#         # 2. Check feedback from responsive motors
#         overheating_motors = []
#         for motor_id in responsive_motors:
#             feedback = self.motor_controller.get_motor_feedback(motor_id)
#             if feedback.get("temperature", 0) > 80: # Critical temperature threshold
#                 overheating_motors.append(motor_id)
        
#         if overheating_motors:
#             warnings.append(f"Motors overheating: {overheating_motors}")
        
#         # Determine overall status
#         if errors:
#             report["status"] = HealthStatus.ERROR.name
#             report["details"]["errors"] = errors
#         if warnings:
#             if report["status"] != HealthStatus.ERROR.name:
#                 report["status"] = HealthStatus.WARNING.name
#             report["details"]["warnings"] = warnings

#         return report

#     def _check_sensor_suite(self) -> Dict[str, Any]:
#         """Runs diagnostics on the sensor suite."""
#         if not self.sensor_suite:
#             return {"status": HealthStatus.UNKNOWN.name, "details": "Module not provided."}

#         statuses = self.sensor_suite.get_all_statuses()
#         inactive_sensors = [name for name, status in statuses.items() if not status.get("is_active")]

#         if inactive_sensors:
#             return {
#                 "status": HealthStatus.ERROR.name,
#                 "details": f"Inactive sensors detected: {inactive_sensors}"
#             }
#         else:
#             return {
#                 "status": HealthStatus.OK.name,
#                 "details": f"All {len(statuses)} sensors are active."
#             }

#     def _check_software_stacks(self) -> Dict[str, Any]:
#         """Runs diagnostics on high-level software modules."""
#         reports = {}
#         if self.navigation_system:
#             status = self.navigation_system.get_status()
#             reports["navigation"] = {
#                 "status": HealthStatus.OK.name,
#                 "details": f"Status is {status.get('status')}"
#             }
#         # Add checks for NLP, Vision, etc. here
#         return reports

#     def run_full_diagnostic(self) -> Dict[str, Any]:
#         """
#         Runs all diagnostic checks and compiles a single, comprehensive report.
#         """
#         logger.info("Running full system diagnostic...")
#         full_report = {
#             "report_timestamp": datetime.now().isoformat(),
#             "overall_status": HealthStatus.OK.name,
#             "components": {}
#         }
        
#         # Run checks for each component
#         component_checks = {
#             "motors": self._check_motor_controller(),
#             "sensors": self._check_sensor_suite(),
#             **self._check_software_stacks()
#         }
        
#         full_report["components"] = component_checks
        
#         # Determine final overall status
#         for component, report in component_checks.items():
#             if report["status"] == HealthStatus.ERROR.name:
#                 full_report["overall_status"] = HealthStatus.ERROR.name
#                 break
#             if report["status"] == HealthStatus.WARNING.name:
#                 full_report["overall_status"] = HealthStatus.WARNING.name
                
#         logger.info(f"Diagnostic complete. Overall Status: {full_report['overall_status']}")
#         return full_report
        
#     def _monitoring_worker(self, interval: int):
#         """Background worker for continuous monitoring."""
#         while not self._stop_event.is_set():
#             report = self.run_full_diagnostic()
#             if report["overall_status"] != HealthStatus.OK.name:
#                 logger.warning(f"CONTINUOUS MONITORING ALERT: System status is {report['overall_status']}. Details: {report['components']}")
#             else:
#                 logger.info("CONTINUOUS MONITORING: System health is OK.")
#             time.sleep(interval)
            
#     def start_continuous_monitoring(self, interval: int = 10):
#         """Starts a background thread to run diagnostics periodically."""
#         if self.monitoring_thread and self.monitoring_thread.is_alive():
#             logger.warning("Continuous monitoring is already active.")
#             return

#         self._stop_event.clear()
#         self.monitoring_thread = threading.Thread(
#             target=self._monitoring_worker,
#             args=(interval,),
#             daemon=True
#         )
#         self.monitoring_thread.start()
#         logger.info(f"Continuous monitoring started with a {interval}-second interval.")
        
#     def stop_continuous_monitoring(self):
#         """Stops the continuous monitoring thread."""
#         if self.monitoring_thread and self.monitoring_thread.is_alive():
#             self._stop_event.set()
#             self.monitoring_thread.join(timeout=2.0)
#             logger.info("Continuous monitoring stopped.")


# # --- Example Usage ---
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== Robotics Diagnostic Tools Prototype 🩺🛠️ ===")
#     print("=========================================================")

#     # 1. Create mock instances of all robotics components
#     # These are configured to show various health statuses.
#     mock_motors = MockMotorController()
#     mock_sensors = MockSensorSuite()
#     mock_nav = MockAINavigationSystem()
#     motor_ids_list = [1, 2, 3, 4, 5, 6]

#     # 2. Initialize the diagnostics tool with all components
#     diagnostics = RoboticsDiagnostics(
#         motor_controller=mock_motors,
#         sensor_suite=mock_sensors,
#         navigation_system=mock_nav,
#         motor_ids=motor_ids_list
#     )

#     # 3. Run a one-time full diagnostic and print the report
#     print("\n--- Running a single, full diagnostic check ---")
#     full_report = diagnostics.run_full_diagnostic()
    
#     import json
#     print(json.dumps(full_report, indent=2))
    
#     # 4. Demonstrate continuous monitoring
#     print("\n\n--- Starting continuous monitoring for 15 seconds (check every 5s) ---")
#     diagnostics.start_continuous_monitoring(interval=5)
#     try:
#         time.sleep(16)
#     except KeyboardInterrupt:
#         pass
#     finally:
#         diagnostics.stop_continuous_monitoring()

#     print("\n=========================================================")
#     print("=== Diagnostics Prototype Complete ===")
#     print("=========================================================")






# Devin/modules/robotics/diagnostic_tools.py
# Purpose: A functional suite of tools for running diagnostics on all
#          robotics components by integrating with other live modules.

import logging
import threading
import time
from datetime import datetime
from enum import Enum, auto
from typing import Dict, Any, Optional, List

try:
    # --- Import the REAL, integrated robotics modules ---
    from modules.robotics.motor_control import MotorController, MotorState
    from modules.robotics.sensor_integration import SensorSuite
    from modules.robotics.ai_navigation import AINavigationSystem, NavigationStatus
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# Configure basic logging
logger = logging.getLogger("RoboticsDiagnostics")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False

class HealthStatus(Enum):
    OK = "OK"
    WARNING = "WARNING"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

class RoboticsDiagnostics:
    """Aggregates status and runs health checks on all robotics components."""
    def __init__(self, motor_controller: MotorController, sensor_suite: SensorSuite, navigation_system: AINavigationSystem, motor_ids: List[int]):
        if not DEVIN_CORE_AVAILABLE:
            raise ImportError(f"A core Devin module is missing. Error: {_import_error}")
        
        self.motor_controller = motor_controller
        self.sensor_suite = sensor_suite
        self.navigation_system = navigation_system
        self.all_motor_ids = motor_ids

    def _check_motor_controller(self) -> Dict[str, Any]:
        """Runs diagnostics on the motor controller and individual motors."""
        report = {"status": HealthStatus.OK.name, "details": {}}
        warnings, errors = [], []

        responsive_motors = []
        for motor_id in self.all_motor_ids:
            feedback = self.motor_controller.get_motor_feedback(motor_id)
            if feedback:
                responsive_motors.append(motor_id)
                # Check for specific hardware issues from feedback
                if getattr(feedback, 'temperature', 0) > 80:
                    warnings.append(f"Motor {motor_id} is overheating (Temp > 80C).")
                if getattr(feedback, 'voltage', 12) < 10.0:
                    warnings.append(f"Motor {motor_id} has low voltage (< 10V).")
            else:
                errors.append(f"Motor {motor_id} is not responding.")
        
        report["details"]["connectivity"] = f"{len(responsive_motors)}/{len(self.all_motor_ids)} motors responding."
        
        if errors:
            report["status"] = HealthStatus.ERROR.name
            report["details"]["errors"] = errors
        if warnings:
            if report["status"] != HealthStatus.ERROR.name:
                report["status"] = HealthStatus.WARNING.name
            report["details"]["warnings"] = warnings

        return report

    def _check_sensor_suite(self) -> Dict[str, Any]:
        """Runs diagnostics on the sensor suite."""
        inactive_sensors = [sid for sid, s in self.sensor_suite.sensors.items() if not s.is_active]
        if inactive_sensors:
            return {"status": HealthStatus.ERROR.name, "details": f"Inactive sensors: {inactive_sensors}"}
        else:
            return {"status": HealthStatus.OK.name, "details": f"All {len(self.sensor_suite.sensors)} sensors are active."}

    def run_full_diagnostic(self) -> Dict[str, Any]:
        """Runs all diagnostic checks and compiles a single, comprehensive report."""
        logger.info("Running full system diagnostic...")
        component_checks = {
            "motors": self._check_motor_controller(),
            "sensors": self._check_sensor_suite(),
            "navigation": {"status": self.navigation_system.status.name}
        }
        
        overall_status = HealthStatus.OK
        for report in component_checks.values():
            status = HealthStatus[report["status"]]
            if status == HealthStatus.ERROR:
                overall_status = HealthStatus.ERROR
                break
            if status == HealthStatus.WARNING:
                overall_status = HealthStatus.WARNING

        return {
            "report_timestamp": datetime.now().isoformat(),
            "overall_status": overall_status.name,
            "components": component_checks
        }

# --- Example Usage with a Dynamic Mock Simulation ---
if __name__ == "__main__":
    import json
    
    print("=========================================================")
    print("=== Integrated Robotics Diagnostic Tools 🩺🛠️ ===")
    print("=========================================================")

    # --- 1. Create a dynamic mock environment that simulates our real modules ---
    class MockDynamicMotorController:
        """A mock that simulates motor failures over time."""
        def __init__(self, motor_ids):
            self.motor_states = {mid: {"temp": 45, "volt": 12.0, "responsive": True} for mid in motor_ids}
            self.start_time = time.time()
        
        def get_motor_feedback(self, motor_id):
            elapsed = time.time() - self.start_time
            # Simulate a motor overheating after 5 seconds
            if motor_id == 2 and elapsed > 5:
                self.motor_states[motor_id]["temp"] = 85
            # Simulate a motor failing completely after 10 seconds
            if motor_id == 4 and elapsed > 10:
                self.motor_states[motor_id]["responsive"] = False

            if not self.motor_states[motor_id]["responsive"]: return None
            return type("MotorState", (), {"temperature": self.motor_states[motor_id]["temp"], "voltage": self.motor_states[motor_id]["volt"]})

    class MockDynamicSensorSuite:
        """A mock that simulates a sensor disconnecting."""
        def __init__(self):
            self.sensors = {
                "wrist_camera": type("Sensor", (), {"is_active": True})(),
                "lidar": type("Sensor", (), {"is_active": True})()
            }
            self.start_time = time.time()
        def check_status(self):
            if time.time() - self.start_time > 15:
                self.sensors["lidar"].is_active = False # LiDAR "disconnects"

    print("\n--- 1. Setting up a dynamic simulation environment ---")
    motor_ids = [1, 2, 3, 4]
    mock_motors = MockDynamicMotorController(motor_ids)
    mock_sensors = MockDynamicSensorSuite()
    # For this demo, navigation system state is static
    mock_nav = type("AINav", (), {"status": NavigationStatus.IDLE})()

    # --- 2. Initialize the real diagnostics tool with the mock components ---
    diagnostics = RoboticsDiagnostics(
        motor_controller=mock_motors,
        sensor_suite=mock_sensors,
        navigation_system=mock_nav,
        motor_ids=motor_ids
    )

    # --- 3. Run diagnostics periodically to see the system state change ---
    print("\n--- 2. Running continuous monitoring for 20 seconds ---")
    print("     (Watch for the 'overall_status' to change as failures are simulated)")
    try:
        for i in range(4):
            print(f"\n--- Diagnostic Check #{i+1} at t={i*5}s ---")
            # In the mock, check for status changes before running the report
            mock_sensors.check_status() 
            
            report = diagnostics.run_full_diagnostic()
            print(json.dumps(report, indent=2))
            
            if report["overall_status"] == "ERROR":
                print("\nCritical ERROR detected. Stopping monitoring.")
                break
            time.sleep(5)
    except KeyboardInterrupt:
        print("Monitoring stopped by user.")

    print("\n=========================================================")
    print("=== Diagnostics Demo Complete ===")
    print("=========================================================")
