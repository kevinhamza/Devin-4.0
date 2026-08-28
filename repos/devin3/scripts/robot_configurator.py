# scripts/robot_configurator.py
from modules.user_interaction_module import UserInteractionManager
import json

def configure_robot():
    print("--- Devin Robot Configuration Wizard ---")
    uim = UserInteractionManager()
    config = {
        "robot_name": uim.get_user_input("Enter a name for your robot:"),
        "serial_port": uim.get_user_input("Enter the serial port for the motor controller (e.g., COM3 or /dev/ttyACM0):"),
        "camera_id": int(uim.get_user_input("Enter the camera device ID (usually 0):")),
        "ultrasonic_pins": {
            "trigger": int(uim.get_user_input("Enter the GPIO pin for the ultrasonic sensor TRIGGER:")),
            "echo": int(uim.get_user_input("Enter the GPIO pin for the ultrasonic sensor ECHO:")),
        }
    }
    with open("robot_config.json", "w") as f:
        json.dump(config, f, indent=2)
    print("\nConfiguration saved to 'robot_config.json'.")

if __name__ == "__main__":
    configure_robot()
