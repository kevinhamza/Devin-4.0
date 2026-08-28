# # Devin/modules/robotics/gesture_control.py
# # Purpose: Provides real-time hand tracking and gesture recognition using a
# #          camera feed, enabling gesture-based control for Devin.

# import logging
# from enum import Enum, auto
# from typing import List, Tuple, Dict, Optional, Callable

# # --- Dependency Installation Notes ---
# # This module requires several powerful libraries.
# #
# # 1. OpenCV: For camera access and image processing.
# #    pip install opencv-python
# #
# # 2. MediaPipe: For hand landmark detection.
# #    pip install mediapipe

# try:
#     import cv2
#     import numpy as np
#     import mediapipe as mp
#     CV_LIBS_AVAILABLE = True
# except ImportError:
#     CV_LIBS_AVAILABLE = False
#     cv2, np, mp = None, None, None
#     logger.error("Required libraries not found! Please run: 'pip install opencv-python mediapipe'. This module will be non-functional.")

# # Configure basic logging
# logger = logging.getLogger("GestureControl")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# class Gesture(Enum):
#     """Enumeration of recognizable gestures."""
#     FIST = auto()
#     OPEN_HAND = auto()
#     THUMBS_UP = auto()
#     POINTING_UP = auto()
#     OKAY = auto()
#     UNKNOWN = auto()
#     # Could be extended with numbers, etc.

# class GestureController:
#     """
#     Analyzes a video stream to detect and classify hand gestures in real-time.
#     """
#     def __init__(self, static_mode=False, max_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.5):
#         """
#         Initializes the MediaPipe hand tracking solution.
#         """
#         if not CV_LIBS_AVAILABLE:
#             self.hands_solution = None
#             logger.error("GestureController could not be initialized due to missing libraries.")
#             return

#         self.hands_solution = mp.solutions.hands.Hands(
#             static_image_mode=static_mode,
#             max_num_hands=max_hands,
#             min_detection_confidence=min_detection_confidence,
#             min_tracking_confidence=min_tracking_confidence
#         )
#         self.mp_drawing = mp.solutions.drawing_utils
#         self._is_running = False
#         logger.info("GestureController initialized with MediaPipe Hands solution.")

#     def _classify_gesture(self, hand_landmarks) -> Gesture:
#         """
#         Applies rule-based logic to classify a gesture from hand landmarks.
#         This is the core logic for recognizing specific gestures.
#         """
#         # Landmark indices for fingertips and other key points
#         TIP_IDS = [4, 8, 12, 16, 20] # Thumb, Index, Middle, Ring, Pinky
        
#         # Get landmark coordinates
#         landmarks = [ (lm.x, lm.y) for lm in hand_landmarks.landmark ]
        
#         # --- Rule-based Gesture Classification ---
#         fingers_up = []
        
#         # Thumb (special case, based on x-coordinate relative to its base)
#         if landmarks[TIP_IDS[0]][0] > landmarks[TIP_IDS[0] - 1][0]: # Right hand check
#              fingers_up.append(1)
#         else:
#              fingers_up.append(0)
             
#         # Other four fingers (based on y-coordinate relative to knuckles below)
#         for i in range(1, 5):
#             if landmarks[TIP_IDS[i]][1] < landmarks[TIP_IDS[i] - 2][1]:
#                 fingers_up.append(1)
#             else:
#                 fingers_up.append(0)
                
#         total_fingers = sum(fingers_up)

#         # Classify based on finger count and positions
#         if total_fingers == 0:
#             return Gesture.FIST
#         elif total_fingers == 5:
#             return Gesture.OPEN_HAND
#         elif total_fingers == 1 and fingers_up[1] == 1:
#             return Gesture.POINTING_UP
#         elif total_fingers == 1 and fingers_up[0] == 1:
#             return Gesture.THUMBS_UP
#         else:
#             return Gesture.UNKNOWN

#     def detect_gesture_in_image(self, image_bgr: np.ndarray) -> Optional[Tuple[Gesture, List]]:
#         """
#         Detects and classifies a gesture from a single image.
        
#         Returns:
#             A tuple of (Gesture, hand_landmarks) or None if no hand is found.
#         """
#         # Flip the image horizontally for a later selfie-view display
#         # and convert the BGR image to RGB.
#         image_rgb = cv2.cvtColor(cv2.flip(image_bgr, 1), cv2.COLOR_BGR2RGB)
        
#         # To improve performance, optionally mark the image as not writeable to
#         # pass by reference.
#         image_rgb.flags.writeable = False
#         results = self.hands_solution.process(image_rgb)
        
#         if results.multi_hand_landmarks:
#             # For simplicity, we'll use the first hand found
#             hand_landmarks = results.multi_hand_landmarks[0]
#             gesture = self._classify_gesture(hand_landmarks)
#             return gesture, hand_landmarks
        
#         return None

#     def start_realtime_detection(self, on_gesture: Callable[[Gesture], None], camera_index: int = 0):
#         """
#         Starts a real-time loop to detect gestures from a webcam feed.

#         Args:
#             on_gesture (Callable[[Gesture], None]): A callback function that is triggered
#                                                     when a new gesture is detected.
#             camera_index (int): The index of the camera to use.
#         """
#         if not self.hands_solution:
#             logger.error("Cannot start detection, solution not initialized.")
#             return

#         cap = cv2.VideoCapture(camera_index)
#         if not cap.isOpened():
#             logger.error(f"Cannot open camera at index {camera_index}.")
#             return
            
#         self._is_running = True
#         logger.info("Starting real-time gesture detection... Press 'q' in the window to quit.")
        
#         last_gesture: Optional[Gesture] = None

#         while cap.isOpened() and self._is_running:
#             success, image = cap.read()
#             if not success:
#                 logger.warning("Ignoring empty camera frame.")
#                 continue

#             detection_result = self.detect_gesture_in_image(image)
            
#             # --- Draw landmarks and report gesture ---
#             display_image = cv2.flip(image, 1) # Flip for selfie view
#             if detection_result:
#                 gesture, landmarks = detection_result
                
#                 # Draw the hand annotations on the image.
#                 self.mp_drawing.draw_landmarks(
#                     display_image,
#                     landmarks,
#                     mp.solutions.hands.HAND_CONNECTIONS)
                
#                 # Display the detected gesture name
#                 cv2.putText(display_image, f"Gesture: {gesture.name}", (10, 50), 
#                             cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

#                 # Trigger the callback only when the gesture changes
#                 if gesture != last_gesture:
#                     on_gesture(gesture)
#                     last_gesture = gesture

#             cv2.imshow('Devin Gesture Control', display_image)
            
#             # Check for quit key
#             if cv2.waitKey(5) & 0xFF == ord('q'):
#                 break
        
#         self._is_running = False
#         cap.release()
#         cv2.destroyAllWindows()
#         logger.info("Real-time gesture detection stopped.")

#     def stop_realtime_detection(self):
#         """Signals the real-time detection loop to stop."""
#         self._is_running = False

# # --- Example Usage ---
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== Robotics Gesture Control Prototype 🖐️🤖 ===")
#     print("=========================================================")

#     if not CV_LIBS_AVAILABLE:
#         print("\nRequired libraries not found. Please see installation notes in the script.")
#     else:
#         # Define a callback function to handle detected gestures
#         def handle_new_gesture(gesture: Gesture):
#             print(f"\n[CALLBACK] New Gesture Detected: {gesture.name}")
#             # Here, you could map gestures to actions:
#             if gesture == Gesture.THUMBS_UP:
#                 print("  -> Action: Acknowledged / Confirm")
#             elif gesture == Gesture.FIST:
#                 print("  -> Action: Stop / Cancel")
#             elif gesture == Gesture.POINTING_UP:
#                 print("  -> Action: Select / Go")

#         # Initialize and start the controller
#         gesture_controller = GestureController()
        
#         print("\nStarting webcam feed for gesture detection.")
#         print("Show your hand to the camera. Press 'q' in the video window to exit.")
        
#         try:
#             gesture_controller.start_realtime_detection(on_gesture=handle_new_gesture)
#         except Exception as e:
#             logger.error(f"An error occurred during real-time detection: {e}")
#             logger.error("This may be due to an issue with camera access or library installation.")

#     print("\n=========================================================")
#     print("=== Gesture Control Prototype Complete ===")
#     print("=========================================================")





# Devin/modules/robotics/gesture_control.py
# Purpose: Provides a real-time, gesture-based HCI by integrating hand
#          tracking with direct mouse and keyboard control.

import logging
from enum import Enum, auto
from typing import List, Tuple, Optional, Callable

try:
    import cv2
    import numpy as np
    import mediapipe as mp
    from modules.keyboard_mouse_control import KeyboardMouseController
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# Configure basic logging
logger = logging.getLogger("GestureControl")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)

class Gesture(Enum):
    """Enumeration of recognizable gestures."""
    FIST = auto()
    OPEN_HAND = auto()
    POINTING = auto()
    THUMBS_UP = auto()
    PEACE = auto()
    UNKNOWN = auto()

class GestureController:
    """Analyzes a video stream to detect and classify hand gestures in real-time."""
    def __init__(self, max_hands=1, min_detection_confidence=0.7):
        if not DEVIN_CORE_AVAILABLE:
            raise ImportError(f"A core Devin module is missing. Error: {_import_error}")
        
        self.hands_solution = mp.solutions.hands.Hands(
            max_num_hands=max_hands,
            min_detection_confidence=min_detection_confidence
        )
        self.mp_drawing = mp.solutions.drawing_utils

    def _classify_gesture(self, hand_landmarks) -> Gesture:
        """Applies rule-based logic to classify a gesture from hand landmarks."""
        landmarks = hand_landmarks.landmark
        
        # Check if fingers are extended by comparing y-coordinates of tips to knuckles
        thumb_tip_up = landmarks[4].y < landmarks[3].y
        index_tip_up = landmarks[8].y < landmarks[6].y
        middle_tip_up = landmarks[12].y < landmarks[10].y
        ring_tip_up = landmarks[16].y < landmarks[14].y
        pinky_tip_up = landmarks[20].y < landmarks[18].y

        fingers_up = [thumb_tip_up, index_tip_up, middle_tip_up, ring_tip_up, pinky_tip_up]
        
        # Classify based on which fingers are up
        if fingers_up == [True, False, False, False, False]:
            return Gesture.THUMBS_UP
        elif fingers_up == [False, True, False, False, False]:
            return Gesture.POINTING
        elif fingers_up == [False, True, True, False, False]:
            return Gesture.PEACE
        elif all(fingers_up):
            return Gesture.OPEN_HAND
        elif not any(fingers_up):
            return Gesture.FIST
        
        return Gesture.UNKNOWN

    def process_frame(self, image_bgr: np.ndarray) -> Tuple[np.ndarray, Optional[Gesture], Optional[Tuple[int, int]]]:
        """Processes a single BGR frame to find gestures and landmarks."""
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False # Performance optimization
        results = self.hands_solution.process(image_rgb)
        image_rgb.flags.writeable = True
        
        gesture = None
        index_fingertip_pos = None

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw landmarks for visualization
                self.mp_drawing.draw_landmarks(image_bgr, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)
                
                # Classify gesture for the first hand found
                if not gesture:
                    gesture = self._classify_gesture(hand_landmarks)
                
                # Get the position of the index fingertip for cursor control
                index_fingertip = hand_landmarks.landmark[8]
                h, w, _ = image_bgr.shape
                index_fingertip_pos = (int(index_fingertip.x * w), int(index_fingertip.y * h))
        
        return image_bgr, gesture, index_fingertip_pos

class GestureToActionMapper:
    """Translates detected gestures into keyboard and mouse actions."""
    def __init__(self, controller: KeyboardMouseController):
        self.controller = controller
        self.last_gesture = None

    def handle_gesture(self, gesture: Gesture, data: dict):
        """The callback function to be triggered when a new gesture is detected."""
        if gesture == self.last_gesture or gesture == Gesture.UNKNOWN:
            # If pointing, continuously update mouse position
            if gesture == Gesture.POINTING and data.get("fingertip_pos"):
                x, y = data["fingertip_pos"]
                self.controller.move_mouse_to(x, y)
            return
        
        logger.info(f"[ACTION MAPPER] New Gesture Detected: {gesture.name}")
        self.last_gesture = gesture

        # Map gestures to actions
        if gesture == Gesture.FIST:
            print("  -> Action: Performing a mouse click.")
            self.controller.mouse_click('left')
        elif gesture == Gesture.THUMBS_UP:
            print("  -> Action: Simulating 'Save' hotkey (Ctrl+S).")
            self.controller.hotkey('ctrl', 's')
        elif gesture == Gesture.PEACE:
            print("  -> Action: Typing a friendly message.")
            self.controller.type_string("Live long and prosper!")
        elif gesture == Gesture.OPEN_HAND:
             print("  -> Action: Acknowledged Open Hand (no action assigned).")


# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Integrated Gesture Control HCI (Live Demo) 🖐️🤖 ===")
    print("=========================================================")

    if not DEVIN_CORE_AVAILABLE:
        print(f"\nERROR: A core module is missing. Error: {_import_error}")
    else:
        print("!!! WARNING: This demo will take control of your MOUSE and KEYBOARD. !!!")
        print("Show gestures to the camera. Press 'q' in the video window to exit.")
        input("Press Enter to begin...")

        try:
            # 1. Initialize all components
            g_controller = GestureController()
            kbm_controller = KeyboardMouseController()
            mapper = GestureToActionMapper(controller=kbm_controller)
            camera = cv2.VideoCapture(0)

            # 2. Start the main real-time loop
            while camera.isOpened():
                success, frame = camera.read()
                if not success: continue

                # Flip for a selfie-view display
                frame = cv2.flip(frame, 1)

                # Process the frame to get gesture and landmark data
                processed_frame, gesture, fingertip_pos = g_controller.process_frame(frame)
                
                # If a gesture is found, have the mapper handle it
                if gesture:
                    mapper.handle_gesture(gesture, {"fingertip_pos": fingertip_pos})
                    # Display the gesture name on the frame
                    cv2.putText(processed_frame, f"Gesture: {gesture.name}", (10, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

                cv2.imshow('Devin Gesture Control HCI', processed_frame)
                
                if cv2.waitKey(5) & 0xFF == ord('q'):
                    break
        
        except Exception as e:
            logger.error(f"Demo failed to run: {e}", exc_info=True)
        finally:
            if 'camera' in locals():
                camera.release()
            cv2.destroyAllWindows()
            print("\n--- Demo Complete ---")
            
    print("\n=========================================================")
    print("=== Gesture Control Prototype Complete ===")
    print("=========================================================")
