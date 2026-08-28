"""
Gesture Recognition Module
This module enables Devin to recognize and interpret hand gestures, allowing control of PC functions and integration with other modules.
"""

import cv2
import mediapipe as mp
import numpy as np
import pyautogui

class GestureRecognition:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(static_image_mode=False, 
                                         max_num_hands=2,
                                         min_detection_confidence=0.7,
                                         min_tracking_confidence=0.7)
        self.mp_draw = mp.solutions.drawing_utils
        self.screen_width, self.screen_height = pyautogui.size()

    def process_frame(self, frame):
        """Process a single frame to detect and classify hand gestures."""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                self.perform_action(hand_landmarks)
        return frame

    def perform_action(self, hand_landmarks):
        """Perform an action based on recognized hand gestures."""
        gesture = self.recognize_gesture(hand_landmarks)
        if gesture == "swipe_left":
            pyautogui.hotkey('alt', 'tab')  # Switch to the next window
        elif gesture == "swipe_right":
            pyautogui.hotkey('ctrl', 'tab')  # Switch browser tabs
        elif gesture == "scroll_up":
            pyautogui.scroll(10)
        elif gesture == "scroll_down":
            pyautogui.scroll(-10)
        elif gesture == "click":
            pyautogui.click()
        elif gesture == "double_click":
            pyautogui.doubleClick()
        elif gesture == "drag":
            pyautogui.dragTo(self.screen_width // 2, self.screen_height // 2, duration=1)

    def recognize_gesture(self, hand_landmarks):
        """Recognize gestures based on landmarks."""
        landmarks = [(lm.x, lm.y) for lm in hand_landmarks.landmark]
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        distance = np.linalg.norm(np.array(thumb_tip) - np.array(index_tip))

        # Define simple gesture logic
        if distance < 0.05:
            return "click"
        elif landmarks[8][1] < landmarks[6][1] and landmarks[12][1] < landmarks[10][1]:
            return "scroll_up"
        elif landmarks[8][1] > landmarks[6][1] and landmarks[12][1] > landmarks[10][1]:
            return "scroll_down"
        # Add more gesture recognition logic as needed
        return None

    def start_camera(self):
        """Start the webcam and process frames in real-time."""
        cap = cv2.VideoCapture(0)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame = self.process_frame(frame)
            cv2.imshow('Gesture Recognition', frame)
            if cv2.waitKey(1) & 0xFF == 27:  # Press 'Esc' to exit
                break
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    gr = GestureRecognition()
    gr.start_camera()
