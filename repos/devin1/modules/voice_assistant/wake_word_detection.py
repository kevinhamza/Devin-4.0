import pvporcupine
import pyaudio
import logging
from threading import Thread, Event
import time

class WakeWordDetector:
    def __init__(self, keyword_model_path, sensitivity=0.5, access_key=None, log_file="wake_word_detection.log", audio_device_index=0):
        self.audio_device_index = audio_device_index
        if access_key is None:
            raise ValueError("An access key is required for Porcupine initialization.")

        self.keyword_model_path = keyword_model_path
        self.sensitivity = sensitivity
        self.access_key = access_key
        self.log_file = log_file
        self.running = False
        self.stream = None
        self.stop_event = Event()

        # Setup logging
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )

        # Initialize Porcupine
        try:
            self.porcupine = pvporcupine.create(
                access_key=self.access_key,
                keyword_paths=[self.keyword_model_path],
                sensitivities=[self.sensitivity]
            )
            logging.info("Initialized Porcupine with the provided keyword model.")
        except Exception as e:
            logging.error(f"Failed to initialize Porcupine: {e}")
            raise

        # Initialize PyAudio
        try:
            self.audio = pyaudio.PyAudio()
        except Exception as e:
            logging.error(f"Failed to initialize PyAudio: {e}")
            raise

    def start_detection(self):
        logging.info("Starting wake word detection...")
        self.running = True
        self.stop_event.clear()

        # Create a new thread and start detection
        detection_thread = Thread(target=self.detect_wake_word)  # No arguments passed here
        detection_thread.daemon = True
        detection_thread.start()  # Start the thread

    def detect_wake_word(self):
        try:
            # Open the audio stream
            self.stream = self.audio.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                input_device_index=self.audio_device_index,
                frames_per_buffer=self.porcupine.frame_length
            )
            logging.info("Audio stream opened for wake word detection.")

            # Continuously capture audio frames
            while self.running:
                audio_frame = self.stream.read(self.porcupine.frame_length, exception_on_overflow=False)
                wake_word_index = self.porcupine.process(audio_frame)

                if wake_word_index >= 0:
                    self.on_wake_word_detected()
                    break  # Optional: stop the detection here or continue as needed

        except Exception as e:
            logging.error(f"Error in wake word detection: {e}")

        finally:
            # Close the stream and terminate PyAudio
            if hasattr(self, 'stream'):
                self.stream.stop_stream()
                self.stream.close()
            self.audio.terminate()
            logging.info("Audio stream closed.")

    def on_wake_word_detected(self):
        logging.info("Wake word detected!")
        print("Wake word detected! Performing the next action...")

    def stop_detection(self):
        logging.info("Stopping wake word detection...")
        self.running = False
        self.stop_event.set()

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            logging.info("Audio stream closed.")

        if self.porcupine:
            self.porcupine.delete()
            logging.info("Porcupine resources released.")

        if self.audio:
            self.audio.terminate()
            logging.info("PyAudio resources terminated.")

if __name__ == "__main__":
    model_path = "modules/voice_assistant/Hey-Devin_en_windows_v3_0_0.ppn"  # Replace with your actual keyword model path
    access_key = "VktnNTGZEo/yIvoys2/9xLkNx6lDGXgLShF1MNSqVvN/UE+HW7zsdw=="  # Replace with your actual access key

    try:
        detector = WakeWordDetector(keyword_model_path=model_path, access_key=access_key)
        detector.start_detection()  # Correctly start detection with this method
        print("Listening for 'Hey Devin'... Press Ctrl+C to stop.")

        # Run the detection in a clean way
        while not detector.stop_event.is_set():
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping wake word detection...")
        detector.stop_detection()
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        print(f"Error: {e}")
