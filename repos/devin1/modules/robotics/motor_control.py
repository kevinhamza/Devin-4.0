"""
Motor Control Module
====================
Handles robot motor control and navigation, enabling precise movement and pathfinding capabilities.
"""

import time
import logging
import RPi.GPIO as GPIO  # For Raspberry Pi motor control
from modules.utils.sensors import DistanceSensor, IMUSensor  # Hypothetical sensor utilities

# Configuration for Motor Control
class MotorControlConfig:
    def __init__(self, motor_pins: dict, pwm_frequency: int = 100):
        """
        Configuration for motor control.

        Args:
            motor_pins (dict): Pin mappings for motors (e.g., left, right).
            pwm_frequency (int): PWM frequency for motor speed control.
        """
        self.motor_pins = motor_pins
        self.pwm_frequency = pwm_frequency

# Motor Control Class
class MotorController:
    def __init__(self, config: MotorControlConfig):
        """
        Initializes the motor controller.

        Args:
            config (MotorControlConfig): Configuration for motor control.
        """
        self.motor_pins = config.motor_pins
        self.pwm_frequency = config.pwm_frequency
        self.pwm_instances = {}
        self._setup_gpio()

    def _setup_gpio(self):
        """
        Sets up GPIO pins and PWM instances.
        """
        logging.info("Setting up GPIO pins for motor control...")
        GPIO.setmode(GPIO.BCM)
        for motor, pins in self.motor_pins.items():
            GPIO.setup(pins['forward'], GPIO.OUT)
            GPIO.setup(pins['backward'], GPIO.OUT)
            self.pwm_instances[motor] = GPIO.PWM(pins['pwm'], self.pwm_frequency)
            self.pwm_instances[motor].start(0)
        logging.info("GPIO setup complete.")

    def set_speed(self, motor: str, speed: int):
        """
        Sets the speed for a specific motor.

        Args:
            motor (str): Motor identifier (e.g., 'left', 'right').
            speed (int): Speed value (0-100).
        """
        if motor in self.pwm_instances:
            logging.info(f"Setting speed for {motor} motor to {speed}%...")
            self.pwm_instances[motor].ChangeDutyCycle(speed)
        else:
            logging.error(f"Motor '{motor}' not found in configuration.")

    def move(self, direction: str, speed: int):
        """
        Moves the robot in a specific direction.

        Args:
            direction (str): Direction to move ('forward', 'backward', 'left', 'right', 'stop').
            speed (int): Speed of movement (0-100).
        """
        logging.info(f"Moving {direction} at speed {speed}...")
        for motor, pins in self.motor_pins.items():
            if direction == 'forward':
                GPIO.output(pins['forward'], GPIO.HIGH)
                GPIO.output(pins['backward'], GPIO.LOW)
                self.set_speed(motor, speed)
            elif direction == 'backward':
                GPIO.output(pins['forward'], GPIO.LOW)
                GPIO.output(pins['backward'], GPIO.HIGH)
                self.set_speed(motor, speed)
            elif direction == 'stop':
                GPIO.output(pins['forward'], GPIO.LOW)
                GPIO.output(pins['backward'], GPIO.LOW)
                self.set_speed(motor, 0)
            # Additional directions for turning
            elif direction == 'left':
                if motor == 'left':
                    self.set_speed(motor, 0)  # Stop left motor
                else:
                    GPIO.output(pins['forward'], GPIO.HIGH)
                    GPIO.output(pins['backward'], GPIO.LOW)
                    self.set_speed(motor, speed)
            elif direction == 'right':
                if motor == 'right':
                    self.set_speed(motor, 0)  # Stop right motor
                else:
                    GPIO.output(pins['forward'], GPIO.HIGH)
                    GPIO.output(pins['backward'], GPIO.LOW)
                    self.set_speed(motor, speed)

    def cleanup(self):
        """
        Cleans up GPIO resources.
        """
        logging.info("Cleaning up GPIO resources...")
        for pwm in self.pwm_instances.values():
            pwm.stop()
        GPIO.cleanup()

# Example usage
if __name__ == "__main__":
    motor_config = MotorControlConfig(
        motor_pins={
            'left': {'forward': 17, 'backward': 18, 'pwm': 27},
            'right': {'forward': 22, 'backward': 23, 'pwm': 24}
        }
    )
    motor_controller = MotorController(motor_config)
    try:
        motor_controller.move('forward', 50)
        time.sleep(2)
        motor_controller.move('left', 50)
        time.sleep(1)
        motor_controller.move('stop', 0)
    finally:
        motor_controller.cleanup()
