"""
Keyboard and Mouse Control Prototypes
--------------------------------------
This module provides prototypes for automating keyboard and mouse interactions.
It is designed to control system input devices programmatically to perform actions
such as typing, clicking, and moving the mouse cursor.

Dependencies:
- pyautogui
- keyboard

Ensure the required libraries are installed before using this module.
"""

import pyautogui
import keyboard
import time

class KeyboardMouseController:
    """
    A class to handle keyboard and mouse automation tasks.
    """

    def __init__(self):
        print("Keyboard and Mouse Controller initialized.")

    # Keyboard Control Methods
    def type_text(self, text: str, interval: float = 0.1):
        """
        Types the provided text using the keyboard.

        Args:
            text (str): The text to type.
            interval (float): The delay between each key press (default is 0.1 seconds).
        """
        print(f"Typing text: {text}")
        pyautogui.write(text, interval=interval)

    def press_key(self, key: str):
        """
        Presses a single key.

        Args:
            key (str): The key to press (e.g., 'enter', 'shift', 'a').
        """
        print(f"Pressing key: {key}")
        pyautogui.press(key)

    def hotkey(self, *keys):
        """
        Performs a combination of key presses (hotkey).

        Args:
            *keys: Sequence of keys to press together (e.g., 'ctrl', 'alt', 'del').
        """
        print(f"Executing hotkey: {' + '.join(keys)}")
        pyautogui.hotkey(*keys)

    def hold_key(self, key: str, duration: float = 1.0):
        """
        Holds a key for a specified duration.

        Args:
            key (str): The key to hold.
            duration (float): Duration in seconds to hold the key.
        """
        print(f"Holding key: {key} for {duration} seconds.")
        pyautogui.keyDown(key)
        time.sleep(duration)
        pyautogui.keyUp(key)

    # Mouse Control Methods
    def move_mouse(self, x: int, y: int, duration: float = 0.5):
        """
        Moves the mouse cursor to the specified coordinates.

        Args:
            x (int): X-coordinate on the screen.
            y (int): Y-coordinate on the screen.
            duration (float): Time to take to move the mouse.
        """
        print(f"Moving mouse to ({x}, {y}) over {duration} seconds.")
        pyautogui.moveTo(x, y, duration=duration)

    def click_mouse(self, button: str = 'left'):
        """
        Clicks the mouse.

        Args:
            button (str): Button to click ('left', 'right', 'middle').
        """
        print(f"Clicking mouse button: {button}")
        pyautogui.click(button=button)

    def scroll_mouse(self, clicks: int):
        """
        Scrolls the mouse.

        Args:
            clicks (int): Number of scroll clicks (positive for up, negative for down).
        """
        print(f"Scrolling mouse by {clicks} clicks.")
        pyautogui.scroll(clicks)

    # Advanced Control
    def record_keyboard_events(self, duration: float = 10.0):
        """
        Records keyboard events for a specified duration.

        Args:
            duration (float): Duration in seconds to record events.
        """
        print(f"Recording keyboard events for {duration} seconds. Press 'esc' to stop.")
        events = []
        start_time = time.time()
        while time.time() - start_time < duration:
            event = keyboard.read_event(suppress=True)
            if event.name == 'esc':  # Stop recording on 'esc' key press
                print("Recording stopped by user.")
                break
            events.append(event)
            print(f"Recorded event: {event}")
        return events

    def playback_keyboard_events(self, events):
        """
        Plays back recorded keyboard events.

        Args:
            events: A list of recorded keyboard events.
        """
        print(f"Playing back {len(events)} keyboard events.")
        for event in events:
            if event.event_type == 'down':
                pyautogui.press(event.name)
                print(f"Played back key: {event.name}")


if __name__ == "__main__":
    controller = KeyboardMouseController()

    # Example Usage:
    controller.type_text("Hello, this is a test!")
    controller.press_key('enter')
    controller.hotkey('ctrl', 'c')
    controller.move_mouse(500, 500, duration=1)
    controller.click_mouse()
    controller.scroll_mouse(-10)
    events = controller.record_keyboard_events(duration=5)
    controller.playback_keyboard_events(events)
