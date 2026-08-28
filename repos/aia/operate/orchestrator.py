import logging
import time
from modules.voice_assistant import VoiceAssistant
from modules.internet_tasks import InternetTasks
from modules.device_control import DeviceControl
from modules.social_media import SocialMediaManager
from modules.chatbot import ChatBot
from modules.machine_learning import ModelManager
from modules.error_handling import ErrorLogger
from config.settings import Config

class Orchestrator:
    """
    Orchestrates various AI modules and system operations, combining voice recognition,
    task automation, device control, social media interactions, and error handling.
    """

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger("Orchestrator")

        # Initialize modules
        self.voice_assistant = VoiceAssistant(config)
        self.internet_tasks = InternetTasks(config)
        self.device_control = DeviceControl(config)
        self.social_media_manager = SocialMediaManager(config=config)
        self.chatbot = ChatBot(config)
        self.ml = ModelManager(model_type=self.config.get_model_config("MODEL_TYPE"))  # Pass the key name
        self.error_handler = ErrorLogger(log_directory="logs")

        # Register modules
        self.modules = {}
        self.register_module("voice_assistant", self.voice_assistant)
        self.register_module("internet_tasks", self.internet_tasks)
        self.register_module("device_control", self.device_control)
        self.register_module("social_media_manager", self.social_media_manager)
        self.register_module("chatbot", self.chatbot)
        self.register_module("ml", self.ml)
        self.register_module("error_handler", self.error_handler)

    def register_module(self, module_name: str, module_object):
        """
        Registers a module by adding it to the orchestrator's modules dictionary.
        """
        self.modules[module_name] = module_object
        self.logger.info(f"Module '{module_name}' registered successfully.")

    def execute_voice_command(self, command: str):
        """
        Process a voice command, calling the respective method or module.
        """
        try:
            if "weather" in command:
                self.logger.info("Fetching weather information.")
                self.internet_tasks.get_weather()
            elif "news" in command:
                self.logger.info("Fetching news.")
                self.internet_tasks.get_news()
            elif "control" in command:
                self.logger.info("Controlling devices.")
                self.device_control.move_mouse(100, 100)  # Example action
            elif "social" in command:
                self.logger.info("Interacting with social media.")
                if "post to twitter" in command:
                    self.social_media_manager.post_to_twitter("Automated post!")
                elif "fetch twitter posts" in command:
                    self.social_media_manager.get_latest_posts("twitter")
                elif "post to facebook" in command:
                    self.social_media_manager.post_to_facebook("Automated post!")
                else:
                    self.logger.warning("Unknown social media command.")
            elif "chat" in command:
                self.logger.info("Chatbot initiated.")
                self.chatbot.start_chatbot(command)
            else:
                self.logger.warning(f"Unknown command: {command}")
        except Exception as e:
            error_message = self.error_handler.handle_exception(e, "Error in execute_voice_command")
            self.logger.error(error_message)

    def monitor_system(self):
        """
        Monitor the system's performance and handle any system-level requests.
        """
        try:
            while True:
                self.logger.info("System is running...")
                time.sleep(5)
        except KeyboardInterrupt:
            self.logger.info("System monitoring interrupted by user.")

    def run(self):
        """
        Run the orchestrator to handle commands, control the system, and process tasks.
        """
        self.logger.info("Starting Orchestrator...")
        while True:
            try:
                # Simulate receiving a voice command for testing
                command = self.voice_assistant.listen_for_command()
                if command:
                    self.logger.info(f"Received command: {command}")
                    self.execute_voice_command(command)
            except KeyboardInterrupt:
                self.shutdown()
                break
            except Exception as e:
                error_message = self.error_handler.handle_exception(e, "Error in orchestrator.run")
                self.logger.error(error_message)

    def shutdown(self):
        """
        Shutdown the orchestrator and clean up resources.
        """
        self.logger.info("Shutting down orchestrator...")
        try:
            self.voice_assistant.stop_listening()
            self.device_control.shutdown_system()
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
        finally:
            self.logger.info("Orchestrator shut down successfully.")

    def handle_command(self, command: str):
        """
        Handle a command input from the user.
        This method can be expanded to include various commands.
        """
        if command.lower() == "detect face":
            # Call the face detection functionality
            return self.execute_task("face_detection", {})
        elif command.lower() == "recognize person":
            # Call the recognition functionality
            return self.execute_task("face_recognition", {})
        # Add more commands as needed
        else:
            return "Command not recognized."
        
# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    config = Config()
    orchestrator = Orchestrator(config)
    orchestrator.run()
