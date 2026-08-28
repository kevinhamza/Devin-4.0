import pyautogui
from pynput.keyboard import Key, Controller as KeyboardController
from pynput.mouse import Controller as MouseController, Button
import logging

logging.basicConfig(level=logging.INFO)

class control_input:
    """
    Provides functionalities for controlling keyboard and mouse actions.
    """
    def __init__(self):
        self.keyboard = KeyboardController()
        self.mouse = MouseController()

    # --- Keyboard Control Methods ---
    def type_text(self, text: str):
        """
        Simulates typing the given text.
        """
        logging.info(f"Typing text: {text}")
        for char in text:
            self.keyboard.type(char)

    def press_key(self, key: str):
        """
        Presses a specific key.
        """
        logging.info(f"Pressing key: {key}")
        self.keyboard.press(key)
        self.keyboard.release(key)

    def hold_key(self, key: str, duration: float):
        """
        Holds a specific key for a given duration.
        """
        logging.info(f"Holding key: {key} for {duration} seconds")
        self.keyboard.press(key)
        time.sleep(duration)
        self.keyboard.release(key)

    def shortcut(self, *keys):
        """
        Executes a keyboard shortcut.
        """
        logging.info(f"Executing shortcut: {' + '.join(keys)}")
        with self.keyboard.pressed(*keys):
            pass

    # --- Mouse Control Methods ---
    def move_mouse(self, x: int, y: int):
        """
        Moves the mouse to a specific position.
        """
        logging.info(f"Moving mouse to: ({x}, {y})")
        self.mouse.position = (x, y)

    def click_mouse(self, button: str = "left"):
        """
        Simulates a mouse click.
        """
        button_type = Button.left if button == "left" else Button.right
        logging.info(f"Clicking mouse with {button} button")
        self.mouse.click(button_type)

    def scroll_mouse(self, dx: int, dy: int):
        """
        Simulates mouse scrolling.
        """
        logging.info(f"Scrolling mouse by: ({dx}, {dy})")
        self.mouse.scroll(dx, dy)

    def drag_mouse(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 1.0):
        """
        Simulates a mouse drag from one point to another.
        """
        logging.info(f"Dragging mouse from ({start_x}, {start_y}) to ({end_x}, {end_y})")
        pyautogui.moveTo(start_x, start_y, duration=duration)
        pyautogui.dragTo(end_x, end_y, duration=duration)

if __name__ == "__main__":
    controller = KeyboardMouseControl()
    # Example actions
    controller.type_text("Hello, this is a test.")
    controller.press_key("enter")
    controller.move_mouse(100, 200)
    controller.click_mouse("left")
    controller.scroll_mouse(0, -10)
