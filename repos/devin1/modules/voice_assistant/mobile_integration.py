"""
mobile_integration.py
----------------------
This module handles mobile-specific integration for the Devin voice assistant.

Features:
- Connects with mobile device APIs for seamless operation.
- Handles wake word detection, voice recognition, and task execution.
- Cross-platform support for Android and iOS using respective APIs.
"""

import logging
import platform
import os

# Optional imports for mobile integration
try:
    from plyer import notification  # Cross-platform notifications
    import pyttsx3  # Text-to-speech
    import requests  # API communication
except ImportError as e:
    raise ImportError(f"Missing module: {e}. Ensure all dependencies are installed.")

class MobileIntegration:
    """
    A class to handle mobile-specific integration for Devin's voice assistant.
    """

    def __init__(self, api_url, tts_engine="sapi5", log_file="mobile_integration.log"):
        """
        Initializes the mobile integration module.

        Args:
            api_url (str): Base URL for the mobile integration API.
            tts_engine (str): Text-to-speech engine to use.
            log_file (str): Path to the log file.
        """
        self.api_url = api_url
        self.tts_engine = pyttsx3.init(tts_engine)

        # Set up logging
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )
        logging.info("MobileIntegration initialized.")

        # Platform validation
        self.current_platform = platform.system().lower()
        if self.current_platform not in ["android", "ios", "windows", "linux", "darwin"]:
            logging.warning(f"Unsupported platform: {self.current_platform}")
            raise EnvironmentError("Unsupported platform. Mobile integration is only available for Android and iOS.")

    def notify_user(self, title, message):
        """
        Sends a notification to the user's mobile device.

        Args:
            title (str): Notification title.
            message (str): Notification message.
        """
        logging.info(f"Sending notification: {title} - {message}")
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="Devin Voice Assistant"
            )
        except Exception as e:
            logging.error(f"Notification failed: {e}")
            raise

    def send_request_to_mobile_api(self, endpoint, data=None):
        """
        Sends a request to the mobile-specific API.

        Args:
            endpoint (str): API endpoint to hit.
            data (dict): Data payload to send.

        Returns:
            dict: Response from the API.
        """
        url = f"{self.api_url}/{endpoint}"
        logging.info(f"Sending request to API: {url}")
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            logging.info(f"API response: {response.json()}")
            return response.json()
        except Exception as e:
            logging.error(f"API request failed: {e}")
            raise

    def handle_voice_command(self, command):
        """
        Processes the recognized voice command and executes corresponding tasks.

        Args:
            command (str): The recognized voice command.

        Returns:
            str: Response to the voice command.
        """
        logging.info(f"Handling voice command: {command}")
        try:
            if "open app" in command:
                app_name = command.split("open app")[-1].strip()
                return self.open_mobile_app(app_name)
            elif "send message" in command:
                message_details = command.split("send message")[-1].strip()
                return self.send_text_message(message_details)
            else:
                return f"Command '{command}' not recognized."
        except Exception as e:
            logging.error(f"Failed to handle command: {e}")
            return "An error occurred while processing your command."

    def open_mobile_app(self, app_name):
        """
        Opens a specified mobile app.

        Args:
            app_name (str): The name of the app to open.

        Returns:
            str: Status of the operation.
        """
        logging.info(f"Attempting to open app: {app_name}")
        try:
            data = {"app_name": app_name}
            response = self.send_request_to_mobile_api("open_app", data)
            if response.get("status") == "success":
                return f"App '{app_name}' opened successfully."
            else:
                return f"Failed to open app '{app_name}'."
        except Exception as e:
            logging.error(f"Error opening app: {e}")
            return f"Error opening app '{app_name}'."

    def send_text_message(self, message_details):
        """
        Sends a text message via the mobile device.

        Args:
            message_details (str): Details of the message, including recipient and content.

        Returns:
            str: Status of the operation.
        """
        logging.info(f"Sending text message: {message_details}")
        try:
            data = {"message_details": message_details}
            response = self.send_request_to_mobile_api("send_message", data)
            if response.get("status") == "success":
                return "Message sent successfully."
            else:
                return "Failed to send the message."
        except Exception as e:
            logging.error(f"Error sending message: {e}")
            return "Error sending the message."

    def text_to_speech(self, text):
        """
        Converts text to speech and speaks it.

        Args:
            text (str): Text to be spoken.
        """
        logging.info(f"Converting text to speech: {text}")
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            logging.error(f"Text-to-speech failed: {e}")
            raise


if __name__ == "__main__":
    # Example usage
    api_base_url = "http://localhost:5000/api"  # Replace with actual mobile API URL
    mobile_integration = MobileIntegration(api_url=api_base_url)

    print("1. Send a notification")
    print("2. Open a mobile app")
    print("3. Send a text message")
    print("4. Speak a text")

    choice = input("Choose an option (1/2/3/4): ")

    if choice == "1":
        mobile_integration.notify_user("Test Notification", "This is a test notification.")
    elif choice == "2":
        app = input("Enter the app name to open: ")
        print(mobile_integration.open_mobile_app(app))
    elif choice == "3":
        details = input("Enter the message details: ")
        print(mobile_integration.send_text_message(details))
    elif choice == "4":
        text = input("Enter the text to speak: ")
        mobile_integration.text_to_speech(text)
    else:
        print("Invalid choice.")
