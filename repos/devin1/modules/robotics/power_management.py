"""
Power Management Module
=======================
Monitors and manages power consumption and battery status for the robotics system.
Optimizes power usage for different components and alerts on low battery.
"""

import threading
import time
import logging
from datetime import datetime


class Battery:
    """
    Represents the battery used in the robotics system.
    """

    def __init__(self, capacity: float):
        """
        Initializes the battery.

        Args:
            capacity (float): Total battery capacity in watt-hours (Wh).
        """
        self.capacity = capacity  # Total capacity in Wh
        self.current_charge = capacity  # Current charge in Wh
        self.lock = threading.Lock()

    def discharge(self, power: float, duration: float):
        """
        Discharges the battery based on power usage and duration.

        Args:
            power (float): Power consumption in watts (W).
            duration (float): Time of usage in hours (h).
        """
        with self.lock:
            energy_used = power * duration
            self.current_charge -= energy_used
            if self.current_charge < 0:
                self.current_charge = 0
            logging.info(f"[BATTERY] Discharged: {energy_used:.2f} Wh. Remaining: {self.current_charge:.2f} Wh.")

    def charge(self, energy: float):
        """
        Charges the battery.

        Args:
            energy (float): Amount of energy to charge in watt-hours (Wh).
        """
        with self.lock:
            self.current_charge += energy
            if self.current_charge > self.capacity:
                self.current_charge = self.capacity
            logging.info(f"[BATTERY] Charged: {energy:.2f} Wh. Current charge: {self.current_charge:.2f} Wh.")

    def get_status(self) -> dict:
        """
        Returns the battery status.

        Returns:
            dict: Battery status including charge percentage and remaining charge.
        """
        with self.lock:
            charge_percentage = (self.current_charge / self.capacity) * 100
            return {
                "current_charge": self.current_charge,
                "capacity": self.capacity,
                "charge_percentage": charge_percentage,
            }


class PowerManager:
    """
    Manages power consumption and battery monitoring.
    """

    def __init__(self, battery: Battery):
        """
        Initializes the power manager.

        Args:
            battery (Battery): The battery to manage.
        """
        self.battery = battery
        self.low_battery_threshold = 20.0  # Low battery warning threshold in percentage
        self.monitoring = False

    def monitor_battery(self):
        """
        Monitors the battery status and logs warnings for low battery.
        """
        logging.info("[POWER MANAGER] Starting battery monitoring...")
        self.monitoring = True
        while self.monitoring:
            status = self.battery.get_status()
            logging.info(f"[BATTERY STATUS] {status}")
            if status["charge_percentage"] <= self.low_battery_threshold:
                logging.warning("[POWER MANAGER] Low battery warning!")
            time.sleep(5)

    def stop_monitoring(self):
        """
        Stops battery monitoring.
        """
        logging.info("[POWER MANAGER] Stopping battery monitoring...")
        self.monitoring = False

    def optimize_power_usage(self, component_power: dict):
        """
        Optimizes power usage by distributing available power among components.

        Args:
            component_power (dict): Dictionary of components and their power consumption (in watts).
        """
        logging.info("[POWER MANAGER] Optimizing power usage...")
        total_power = sum(component_power.values())
        if total_power > self.battery.current_charge:
            logging.warning("[POWER MANAGER] Insufficient power for all components. Adjusting priorities...")
            scaling_factor = self.battery.current_charge / total_power
            for component, power in component_power.items():
                adjusted_power = power * scaling_factor
                logging.info(f"[POWER MANAGER] Adjusted power for {component}: {adjusted_power:.2f} W.")
        else:
            logging.info("[POWER MANAGER] Power allocation successful for all components.")


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Initialize the battery and power manager
    robot_battery = Battery(capacity=100.0)  # 100 Wh battery
    power_manager = PowerManager(battery=robot_battery)

    # Simulate power usage
    threading.Thread(target=power_manager.monitor_battery).start()

    # Simulate components consuming power
    components = {
        "motors": 20.0,  # 20 W
        "sensors": 5.0,  # 5 W
        "camera": 10.0,  # 10 W
    }
    for _ in range(5):
        robot_battery.discharge(power=35.0, duration=0.5)  # 35 W for 0.5 hours
        time.sleep(3)

    # Stop monitoring
    power_manager.stop_monitoring()
