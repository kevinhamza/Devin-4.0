import logging
import time
from modules.voice_assistant import VoiceAssistant
from modules.internet_tasks import InternetTasks
from modules.device_control import DeviceControl
from modules.social_media import SocialMedia
from modules.chatbot import ChatBot
from modules.machine_learning import MachineLearning
from modules.error_handling import ErrorHandler
from modules.automation import TaskAutomation

class Evaluator:
    """
    Evaluates the system's functionality by running a series of tests
    across different modules like voice assistant, social media, internet tasks, and more.
    """
    def __init__(self):
        self.logger = logging.getLogger("Evaluator")
        self.logger.setLevel(logging.DEBUG)
        
        # Initialize system modules
        self.voice_assistant = VoiceAssistant()
        self.internet_tasks = InternetTasks()
        self.device_control = DeviceControl()
        self.social_media = SocialMedia()
        self.chatbot = ChatBot()
        self.ml = MachineLearning()
        self.task_automation = TaskAutomation()
        self.error_handler = ErrorHandler()

    def evaluate_voice_assistant(self):
        """
        Test the voice assistant's recognition and response functionality.
        """
        self.logger.info("Starting voice assistant evaluation.")
        try:
            voice_command = self.voice_assistant.listen_for_command()
            self.logger.info(f"Received command: {voice_command}")
            self.voice_assistant.respond_to_command(voice_command)
            self.logger.info("Voice assistant evaluation completed successfully.")
        except Exception as e:
            self.logger.error(f"Error during voice assistant evaluation: {e}")
            self.error_handler.log_error(e)

    def evaluate_internet_tasks(self):
        """
        Test internet-based tasks such as fetching weather or news.
        """
        self.logger.info("Starting internet tasks evaluation.")
        try:
            self.internet_tasks.get_weather()
            self.internet_tasks.get_news()
            self.logger.info("Internet tasks evaluation completed successfully.")
        except Exception as e:
            self.logger.error(f"Error during internet tasks evaluation: {e}")
            self.error_handler.log_error(e)

    def evaluate_device_control(self):
        """
        Test controlling IoT and system devices via commands.
        """
        self.logger.info("Starting device control evaluation.")
        try:
            self.device_control.control_device("turn on lights")
            self.device_control.control_device("increase volume")
            self.logger.info("Device control evaluation completed successfully.")
        except Exception as e:
            self.logger.error(f"Error during device control evaluation: {e}")
            self.error_handler.log_error(e)

    def evaluate_social_media(self):
        """
        Test the integration with social media platforms.
        """
        self.logger.info("Starting social media evaluation.")
        try:
            self.social_media.post_update("Hello World!")
            self.logger.info("Social media evaluation completed successfully.")
        except Exception as e:
            self.logger.error(f"Error during social media evaluation: {e}")
            self.error_handler.log_error(e)

    def evaluate_chatbot(self):
        """
        Test the chatbot's conversational abilities.
        """
        self.logger.info("Starting chatbot evaluation.")
        try:
            chatbot_response = self.chatbot.chat("What's the weather today?")
            self.logger.info(f"Chatbot response: {chatbot_response}")
            self.logger.info("Chatbot evaluation completed successfully.")
        except Exception as e:
            self.logger.error(f"Error during chatbot evaluation: {e}")
            self.error_handler.log_error(e)

    def evaluate_ml_models(self):
        """
        Evaluate machine learning models with sample input data.
        """
        self.logger.info("Starting machine learning models evaluation.")
        try:
            ml_result = self.ml.predict("Sample Data")
            self.logger.info(f"Machine learning model result: {ml_result}")
            self.logger.info("Machine learning models evaluation completed successfully.")
        except Exception as e:
            self.logger.error(f"Error during ML models evaluation: {e}")
            self.error_handler.log_error(e)

    def evaluate_task_automation(self):
        """
        Test task automation by running a set of predefined tasks.
        """
        self.logger.info("Starting task automation evaluation.")
        try:
            self.task_automation.run_task("backup files")
            self.task_automation.run_task("system cleanup")
            self.logger.info("Task automation evaluation completed successfully.")
        except Exception as e:
            self.logger.error(f"Error during task automation evaluation: {e}")
            self.error_handler.log_error(e)

    def run_all_tests(self):
        """
        Run all evaluations to test the full system.
        """
        self.logger.info("Starting full system evaluation.")
        self.evaluate_voice_assistant()
        self.evaluate_internet_tasks()
        self.evaluate_device_control()
        self.evaluate_social_media()
        self.evaluate_chatbot()
        self.evaluate_ml_models()
        self.evaluate_task_automation()
        self.logger.info("Full system evaluation completed.")

# Example usage:
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    evaluator = Evaluator()

    try:
        evaluator.run_all_tests()
    except Exception as e:
        logging.error(f"Error during evaluation: {e}")
