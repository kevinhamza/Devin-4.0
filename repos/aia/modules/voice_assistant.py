import os
import time
import pyttsx3
import speech_recognition as sr
from modules.error_handling import ErrorLogger
from modules.internet_tasks import InternetTasks

class VoiceAssistant:
    """
    Voice Assistant for interaction with the user via voice commands.
    """
    def __init__(self, config):
        self.config = config
        self.speech_engine = pyttsx3.init()
        self.speech_engine.setProperty("rate", 150)
        self.speech_engine.setProperty("volume", 0.9)
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.error_logger = ErrorLogger()
        self.internet_tasks = InternetTasks()

    def speak(self, text):
        """
        Converts text to speech.
        """
        try:
            self.speech_engine.say(text)
            self.speech_engine.runAndWait()
        except Exception as e:
            self.error_logger.log_error("[VoiceAssistant][speak]", str(e))

    def listen(self):
        """
        Captures audio input and converts it to text.
        """
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print("Listening...")
                audio = self.recognizer.listen(source, timeout=10)
                return self.recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            self.speak("Sorry, I couldn't understand. Could you repeat?")
        except sr.RequestError as e:
            self.error_logger.log_error("[VoiceAssistant][listen]", str(e))
            self.speak("Sorry, I am having trouble connecting to the speech service.")
        except Exception as e:
            self.error_logger.log_error("[VoiceAssistant][listen]", str(e))
            self.speak("An error occurred while listening.")

    def process_command(self, command):
        """
        Processes the voice command and executes corresponding actions.
        """
        command = command.lower()
        if "weather" in command:
            self.handle_weather_request()
        elif "news" in command:
            self.handle_news_request()
        elif "time" in command:
            self.tell_time()
        else:
            self.speak("Sorry, I didn't understand that command.")

    def handle_weather_request(self):
        """
        Fetches and speaks weather information.
        """
        try:
            weather_info = self.internet_tasks.fetch_weather()
            self.speak(f"The current weather is: {weather_info}")
        except Exception as e:
            self.error_logger.log_error("[VoiceAssistant][handle_weather_request]", str(e))
            self.speak("I couldn't fetch the weather information.")

    def handle_news_request(self):
        """
        Fetches and speaks news headlines.
        """
        try:
            news_headlines = self.internet_tasks.fetch_news()
            self.speak("Here are the top news headlines:")
            for headline in news_headlines[:5]:
                self.speak(headline)
        except Exception as e:
            self.error_logger.log_error("[VoiceAssistant][handle_news_request]", str(e))
            self.speak("I couldn't fetch the news headlines.")

    def tell_time(self):
        """
        Tells the current time.
        """
        try:
            current_time = time.strftime("%I:%M %p")
            self.speak(f"The current time is {current_time}")
        except Exception as e:
            self.error_logger.log_error("[VoiceAssistant][tell_time]", str(e))
            self.speak("I couldn't fetch the current time.")

    def start(self):
        """
        Starts the voice assistant loop.
        """
        self.speak("Hello, I am your voice assistant. How can I help you today?")
        while True:
            try:
                command = self.listen()
                if command:
                    if "exit" in command or "quit" in command:
                        self.speak("Goodbye!")
                        break
                    self.process_command(command)
            except KeyboardInterrupt:
                self.speak("Shutting down. Goodbye!")
                break
            except Exception as e:
                self.error_logger.log_error("[VoiceAssistant][start]", str(e))
                self.speak("An error occurred in the main loop.")

# Example usage:
# if __name__ == "__main__":
#     assistant = VoiceAssistant(config)
#     assistant.start()
