# # Devin/modules/keyboard_mouse_control.py
# # Purpose: Provides a low-level, direct interface for controlling
# #          and monitoring keyboard and mouse peripherals.
# # Controls input peripherals ⌨️🖱️

# import logging
# import time
# import random
# from enum import Enum
# from typing import Tuple, Optional, Callable, Any

# # Configure basic logging
# logger = logging.getLogger("PeripheralController")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# class MouseButton(Enum):
#     """Enumeration for mouse buttons."""
#     LEFT = "left"
#     RIGHT = "right"
#     MIDDLE = "middle"

# class SpecialKey:
#     """Namespace for special keyboard key constants."""
#     ENTER = "<enter>"
#     ESC = "<esc>"
#     SHIFT = "<shift>"
#     CTRL = "<ctrl>"
#     ALT = "<alt>"
#     TAB = "<tab>"
#     BACKSPACE = "<backspace>"
#     F1 = "<f1>"
#     # Add other keys as needed...

# class KeyboardMouseController:
#     """
#     Conceptually provides low-level control of keyboard and mouse peripherals.
#     In a real system, this would be a wrapper around a library like 'pynput'.
#     """
#     def __init__(self):
#         self.screen_width, self.screen_height = self._get_screen_size_conceptual()
#         self._mouse_position = (self.screen_width // 2, self.screen_height // 2)
#         logger.info(f"KeyboardMouseController initialized. Conceptual screen size: {self.screen_width}x{self.screen_height}")
#         logger.warning("All peripheral control actions are conceptual and simulate physical hardware events.")

#     def _get_screen_size_conceptual(self) -> Tuple[int, int]:
#         """Simulates getting screen dimensions."""
#         return (1920, 1080)

#     # --- Mouse Control Methods ---
#     def get_mouse_position(self) -> Tuple[int, int]:
#         """Conceptually gets the current (x, y) position of the mouse."""
#         logger.info("CONCEPTUAL PYNPUT: Getting mouse.position")
#         return self._mouse_position

#     def move_mouse_to(self, x: int, y: int) -> None:
#         """Conceptually moves the mouse to an absolute (x, y) screen coordinate."""
#         x = min(max(0, x), self.screen_width)
#         y = min(max(0, y), self.screen_height)
#         logger.info(f"CONCEPTUAL PYNPUT: Setting mouse.position = ({x}, {y})")
#         self._mouse_position = (x, y)

#     def move_mouse_relative(self, dx: int, dy: int) -> None:
#         """Conceptually moves the mouse by a relative offset (dx, dy)."""
#         logger.info(f"CONCEPTUAL PYNPUT: Calling mouse.move({dx}, {dy})")
#         current_x, current_y = self._mouse_position
#         self.move_mouse_to(current_x + dx, current_y + dy)

#     def press_mouse_button(self, button: MouseButton = MouseButton.LEFT) -> None:
#         """Conceptually presses and holds down a mouse button."""
#         logger.info(f"CONCEPTUAL PYNPUT: Calling mouse.press(Button.{button.name.lower()})")

#     def release_mouse_button(self, button: MouseButton = MouseButton.LEFT) -> None:
#         """Conceptually releases a mouse button."""
#         logger.info(f"CONCEPTUAL PYNPUT: Calling mouse.release(Button.{button.name.lower()})")

#     def click_mouse(self, button: MouseButton = MouseButton.LEFT, clicks: int = 1) -> None:
#         """Conceptually performs one or more full clicks."""
#         logger.info(f"CONCEPTUAL PYNPUT: Calling mouse.click(Button.{button.name.lower()}, {clicks})")
#         # Simulates the press and release action
#         self.press_mouse_button(button)
#         time.sleep(0.05) # Brief delay
#         self.release_mouse_button(button)
#         if clicks > 1: # Naive simulation of multiple clicks
#             for _ in range(clicks - 1):
#                 time.sleep(0.05)
#                 self.press_mouse_button(button)
#                 time.sleep(0.05)
#                 self.release_mouse_button(button)

#     def scroll_mouse(self, dy: int, dx: int = 0) -> None:
#         """
#         Conceptually scrolls the mouse wheel vertically or horizontally.
        
#         Args:
#             dy (int): Vertical scroll amount. Positive for down, negative for up.
#             dx (int): Horizontal scroll amount.
#         """
#         logger.info(f"CONCEPTUAL PYNPUT: Calling mouse.scroll({dx}, {dy})")

#     # --- Keyboard Control Methods ---
#     def press_key(self, key: str) -> None:
#         """Conceptually presses and holds down a specific key."""
#         logger.info(f"CONCEPTUAL PYNPUT: Calling keyboard.press('{key}')")

#     def release_key(self, key: str) -> None:
#         """Conceptually releases a specific key."""
#         logger.info(f"CONCEPTUAL PYNPUT: Calling keyboard.release('{key}')")

#     def tap_key(self, key: str) -> None:
#         """Conceptually presses and immediately releases a key."""
#         logger.info(f"CONCEPTUAL PYNPUT: Calling keyboard.tap('{key}')")
#         self.press_key(key)
#         time.sleep(0.01)
#         self.release_key(key)

#     def type_string(self, text: str) -> None:
#         """Conceptually types a string of characters."""
#         logger.info(f"CONCEPTUAL PYNPUT: Calling keyboard.type('{text[:30]}...')")

#     def hotkey(self, *keys: str) -> None:
#         """
#         Conceptually presses and releases a combination of keys in sequence.
#         e.g., hotkey(SpecialKey.CTRL, 'c')
#         """
#         logger.info(f"CONCEPTUAL PYNPUT: Simulating hotkey combination: {keys}")
#         # Press all keys in order
#         for key in keys:
#             self.press_key(key)
#             time.sleep(0.02)
#         # Release all keys in reverse order
#         for key in reversed(keys):
#             self.release_key(key)

#     # --- Conceptual Listener ---
#     def start_listener_conceptual(self,
#                                   on_mouse_click: Optional[Callable[[int, int, MouseButton, bool], Any]] = None,
#                                   on_key_press: Optional[Callable[[str], Any]] = None,
#                                   duration_sec: int = 5) -> None:
#         """
#         Conceptually starts listeners for mouse and keyboard events for a short duration.
#         In a real system, this would be a blocking call or run in a separate thread.
#         """
#         logger.info(f"CONCEPTUAL PYNPUT: Starting event listeners for {duration_sec} seconds...")
        
#         end_time = time.time() + duration_sec
#         while time.time() < end_time:
#             # Simulate random events
#             if random.random() < 0.2: # 20% chance of an event per tick
#                 if random.random() < 0.5 and on_key_press: # Key press event
#                     key = random.choice(['a', 'b', 'c', SpecialKey.ENTER])
#                     logger.info(f"  -> Conceptual Listener DETECTED key press: {key}")
#                     on_key_press(key)
#                 elif on_mouse_click: # Mouse click event
#                     x, y = (random.randint(0, self.screen_width), random.randint(0, self.screen_height))
#                     button = MouseButton.LEFT
#                     logger.info(f"  -> Conceptual Listener DETECTED mouse click: {button.name} at ({x}, {y})")
#                     on_mouse_click(x, y, button, True) # True for pressed
#             time.sleep(0.5)
        
#         logger.info("Conceptual event listeners stopped.")


# # --- Example Usage ---
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== Keyboard & Mouse Controller Prototype ⌨️🖱️ ===")
#     print("=========================================================")
    
#     controller = KeyboardMouseController()

#     print("\n--- Demonstrating Granular Mouse Control ---")
#     start_pos = controller.get_mouse_position()
#     print(f"  Initial mouse position: {start_pos}")
#     controller.move_mouse_to(100, 200)
#     print(f"  Moved to absolute position: {controller.get_mouse_position()}")
#     controller.move_mouse_relative(50, -30)
#     print(f"  Moved to relative position: {controller.get_mouse_position()}")
#     print("  Performing a right-click...")
#     controller.click_mouse(MouseButton.RIGHT)
#     print("  Scrolling down...")
#     controller.scroll_mouse(dy=5) # Scroll down by 5 "units"

#     print("\n\n--- Demonstrating Granular Keyboard Control ---")
#     print("  Typing a sentence...")
#     controller.type_string("Hello, Devin!")
#     print("  Pressing Enter...")
#     controller.tap_key(SpecialKey.ENTER)
    
#     print("\n  Simulating 'Copy' hotkey (Ctrl+C)...")
#     # This sequence demonstrates holding a modifier key
#     controller.press_key(SpecialKey.CTRL)
#     controller.tap_key('c')
#     controller.release_key(SpecialKey.CTRL)
    
#     print("\n  Using the hotkey convenience function for 'Paste' (Ctrl+V)...")
#     controller.hotkey(SpecialKey.CTRL, 'v')


#     print("\n\n--- Demonstrating Drag and Drop Simulation ---")
#     print("  Simulating dragging a file from (400, 400) to (800, 500)")
#     controller.move_mouse_to(400, 400)
#     controller.press_mouse_button(MouseButton.LEFT) # Press and hold
#     time.sleep(0.1)
#     controller.move_mouse_to(800, 500) # Move while holding
#     time.sleep(0.1)
#     controller.release_mouse_button(MouseButton.LEFT) # Release to "drop"


#     print("\n\n--- Demonstrating Conceptual Event Listener ---")
#     # Define simple callback functions
#     def handle_key(key):
#         print(f"    [Callback Executed] Key '{key}' was pressed.")

#     def handle_click(x, y, button, pressed):
#         print(f"    [Callback Executed] Mouse {button.name} {'pressed' if pressed else 'released'} at ({x},{y}).")
        
#     controller.start_listener_conceptual(on_mouse_click=handle_click, on_key_press=handle_key, duration_sec=3)


#     print("\n=========================================================")
#     print("=== Controller Prototype Complete ===")
#     print("=========================================================")



# Devin/modules/keyboard_mouse_control.py
# Purpose: A functional, low-level interface for controlling and monitoring
#          keyboard and mouse peripherals using the 'pynput' library.

import logging
import time
from typing import Tuple, Optional, Callable, Any

try:
    from pynput import mouse, keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False


# Configure basic logging
logger = logging.getLogger("PeripheralController")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)


class KeyboardMouseController:
    """
    Provides low-level control of keyboard and mouse peripherals using 'pynput'.
    """
    def __init__(self):
        if not PYNPUT_AVAILABLE:
            raise ImportError("Pynput library is required. 'pip install pynput'")
        
        self.mouse_controller = mouse.Controller()
        self.keyboard_controller = keyboard.Controller()
        logger.info("KeyboardMouseController initialized with live pynput controllers.")
        logger.warning("This module will take control of your mouse and keyboard during demos.")

        # --- Key mapping for special keys ---
        self.key_map = {
            'enter': keyboard.Key.enter, 'esc': keyboard.Key.esc,
            'shift': keyboard.Key.shift, 'ctrl': keyboard.Key.ctrl, 'alt': keyboard.Key.alt,
            'tab': keyboard.Key.tab, 'backspace': keyboard.Key.backspace,
            'space': keyboard.Key.space, 'up': keyboard.Key.up, 'down': keyboard.Key.down,
            'left': keyboard.Key.left, 'right': keyboard.Key.right,
            'f1': keyboard.Key.f1, 'f2': keyboard.Key.f2, 'f3': keyboard.Key.f3,
            'f4': keyboard.Key.f4, 'f5': keyboard.Key.f5, 'f6': keyboard.Key.f6,
            'f7': keyboard.Key.f7, 'f8': keyboard.Key.f8, 'f9': keyboard.Key.f9,
            'f10': keyboard.Key.f10, 'f11': keyboard.Key.f11, 'f12': keyboard.Key.f12,
            'cmd': keyboard.Key.cmd, 'alt_gr': keyboard.Key.alt_gr,
            'caps_lock': keyboard.Key.caps_lock, 'delete': keyboard.Key.delete,
            'end': keyboard.Key.end, 'home': keyboard.Key.home,
            'insert': keyboard.Key.insert, 'page_down': keyboard.Key.page_down,
            'page_up': keyboard.Key.page_up, 'print_screen': keyboard.Key.print_screen,
        }

    # --- Mouse Control Methods ---
    def get_mouse_position(self) -> Tuple[int, int]:
        """Gets the current (x, y) position of the mouse."""
        return self.mouse_controller.position

    def move_mouse_to(self, x: int, y: int):
        """Moves the mouse to an absolute (x, y) screen coordinate."""
        self.mouse_controller.position = (x, y)

    def move_mouse_relative(self, dx: int, dy: int):
        """Moves the mouse by a relative offset (dx, dy)."""
        self.mouse_controller.move(dx, dy)

    def mouse_click(self, button_name: str = 'left', clicks: int = 1):
        """Performs one or more full clicks."""
        button = getattr(mouse.Button, button_name, mouse.Button.left)
        self.mouse_controller.click(button, clicks)

    def scroll_mouse(self, dy: int, dx: int = 0):
        """Scrolls the mouse wheel vertically or horizontally."""
        self.mouse_controller.scroll(dx, dy)

    # --- Keyboard Control Methods ---
    def _get_key_object(self, key: str):
        """Helper to get a pynput Key object or a character."""
        return self.key_map.get(key.lower(), key)

    def press_key(self, key: str):
        """Presses and holds down a specific key."""
        self.keyboard_controller.press(self._get_key_object(key))

    def release_key(self, key: str):
        """Releases a specific key."""
        self.keyboard_controller.release(self._get_key_object(key))

    def type_string(self, text: str):
        """Types a string of characters."""
        self.keyboard_controller.type(text)

    def hotkey(self, *keys: str):
        """
        Presses and releases a combination of keys.
        e.g., hotkey('ctrl', 'c')
        """
        key_objects = [self._get_key_object(k) for k in keys]
        for key_obj in key_objects:
            self.keyboard_controller.press(key_obj)
        
        # Release in reverse order
        for key_obj in reversed(key_objects):
            self.keyboard_controller.release(key_obj)


# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Integrated Keyboard & Mouse Controller ⌨️🖱️ ===")
    print("=========================================================")
    
    if not PYNPUT_AVAILABLE:
        print("\nERROR: Pynput library is missing. Please run 'pip install pynput'.")
    else:
        print("!!! WARNING: This demo will take control of your mouse and keyboard in 5 seconds. !!!")
        print("!!! To stop the demo, move your mouse to any corner of the screen. !!!")
        time.sleep(5)

        controller = KeyboardMouseController()

        try:
            # --- 1. Mouse Movement and Clicking Demo ---
            print("\n--- 1. Demonstrating Mouse Control ---")
            start_pos = controller.get_mouse_position()
            print(f"  Initial mouse position: {start_pos}")
            
            # Move in a small square
            print("  Moving mouse in a square...")
            controller.move_mouse_relative(100, 0)
            time.sleep(0.5)
            controller.move_mouse_relative(0, 100)
            time.sleep(0.5)
            controller.move_mouse_relative(-100, 0)
            time.sleep(0.5)
            controller.move_mouse_relative(0, -100)
            time.sleep(0.5)
            
            print("  Performing a double-click...")
            controller.mouse_click('left', clicks=2)
            time.sleep(1)

            # --- 2. Keyboard Typing and Hotkey Demo ---
            # This is platform-dependent. We'll try to open a text editor.
            # Windows: Win+R -> notepad -> Enter
            # macOS: Cmd+Space -> TextEdit -> Enter
            # Linux (GNOME): Alt+F2 -> gedit -> Enter
            print("\n--- 2. Demonstrating Keyboard Control ---")
            print("  Attempting to open a text editor and type...")
            
            import platform
            system = platform.system()
            if system == "Windows":
                controller.hotkey('cmd', 'r') # Win+R to open Run dialog
                time.sleep(1)
                controller.type_string('notepad')
                time.sleep(0.5)
                controller.press_key('enter')
                controller.release_key('enter')
            elif system == "Darwin": # macOS
                controller.hotkey('cmd', 'space')
                time.sleep(1)
                controller.type_string('TextEdit')
                time.sleep(1)
                controller.press_key('enter')
                controller.release_key('enter')
            else: # Assume a GNOME-like Linux
                controller.hotkey('alt', 'f2')
                time.sleep(1)
                controller.type_string('gedit') # or 'kate' for KDE
                time.sleep(0.5)
                controller.press_key('enter')
                controller.release_key('enter')

            time.sleep(2) # Wait for the editor to open
            
            controller.type_string("Hello from the Devin AI! This text is being typed automatically. 🤖\n")
            time.sleep(1)
            
            print("  Demonstrating a 'Save As' hotkey (Ctrl+Shift+S)...")
            controller.hotkey('ctrl', 'shift', 's')
            time.sleep(2)
            
            print("  Typing filename and closing dialog...")
            controller.type_string("devin_automated_test.txt")
            time.sleep(1)
            # Press Escape to close the save dialog without saving
            controller.press_key('esc')
            controller.release_key('esc')
            
        except Exception as e:
            logger.error(f"An error occurred during the demo: {e}", exc_info=True)
        finally:
            print("\n--- Demo Complete ---")


    print("\n=========================================================")
    print("=== Controller Prototype Complete ===")
    print("=========================================================")
