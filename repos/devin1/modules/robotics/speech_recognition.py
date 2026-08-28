"""
Speech Recognition Module
==========================
Handles real-time speech-to-text transcription and command interpretation for robotics applications.
"""

import speech_recognition as sr
import logging


class SpeechRecognition:
    """
    A class to handle speech recognition and interpretation.
    """

    def __init__(self):
        """
        Initializes the speech recognition module.
        """
        print("[INFO] Initializing Speech Recognition Module...")
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

    def calibrate_microphone(self, duration=3):
        """
        Calibrates the microphone for ambient noise.

        Args:
            duration (int): Duration to listen for ambient noise calibration.
        """
        print("[INFO] Calibrating microphone for ambient noise...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=duration)
            print(f"[INFO] Ambient noise level set to {self.recognizer.energy_threshold}")

    def transcribe_speech(self, timeout=5, phrase_time_limit=10):
        """
        Captures and transcribes speech from the microphone.

        Args:
            timeout (int): Time to wait for speech input.
            phrase_time_limit (int): Maximum duration of speech input.

        Returns:
            str: The transcribed text.
        """
        print("[INFO] Listening for speech...")
        with self.microphone as source:
            try:
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                transcription = self.recognizer.recognize_google(audio)
                logging.info(f"Transcription: {transcription}")
                return transcription
            except sr.WaitTimeoutError:
                print("[WARNING] No speech detected in the given time.")
                return "Timeout: No speech detected."
            except sr.UnknownValueError:
                print("[WARNING] Speech was unclear or unrecognizable.")
                return "Error: Unable to understand speech."
            except sr.RequestError as e:
                logging.error(f"Speech recognition service error: {e}")
                return "Error: Speech recognition service is unavailable."

    def interpret_command(self, transcription):
        """
        Interprets the given transcription into a robot command.

        Args:
            transcription (str): Transcribed speech.

        Returns:
            str: Robot command.
        """
        print(f"[INFO] Interpreting command from transcription: {transcription}")
        commands = {
            "move forward": "Moving Forward",
            "move backward": "Moving Backward",
            "turn left": "Turning Left",
            "turn right": "Turning Right",
            "stop": "Stopping",
        }
        transcription_lower = transcription.lower()
        for key, action in commands.items():
            if key in transcription_lower:
                return action
        return "Command not recognized."

    def execute_speech_command(self):
        """
        Captures speech, interprets the command, and outputs the robot action.

        Returns:
            str: Executed robot action.
        """
        transcription = self.transcribe_speech()
        if "Error" in transcription or "Timeout" in transcription:
            return transcription
        command = self.interpret_command(transcription)
        print(f"[INFO] Executed Command: {command}")
        return command


# Example usage
if __name__ == "__main__":
    speech_recognition = SpeechRecognition()
    speech_recognition.calibrate_microphone()
    print("[INFO] Starting speech recognition...")
    while True:
        print("[INFO] Speak a command (say 'stop' to end):")
        result = speech_recognition.execute_speech_command()
        if result.lower() == "stopping":
            print("[INFO] Exiting speech recognition module.")
            break
        print(f"[RESULT] {result}")
