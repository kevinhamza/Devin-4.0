import os
import sys
import logging
from modules.voice_assistant import VoiceAssistant
from modules.system_control import SystemControl
from modules.gesture_recognition import GestureRecognition
from modules.ai_tools.ai_learning import AILearning
from operate.analytics import Analytics
from cloud.aws_integration import AWSIntegration
from cloud.gcp_integration import GCPIntegration
from cloud.azure_integration import AzureIntegration
from monitoring.cpu_usage import CPUUsage
from monitoring.analytics_dashboard import AnalyticsDashboard
from scripts.initialize_db import initialize_database
from security.threat_modeling import ThreatModeling
from modules.nlp_conversation import NLPConversation
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def initialize_services():
    """Initialize all required services and dependencies."""
    try:
        # Retrieve arguments from .env file
        db_path = os.getenv("DB_PATH", "")
        data_key = os.getenv("DATA_KEY", "")
        backup_path = os.getenv("BACKUP_PATH", "")

        # Debug: Check the values of the environment variables
        logger.debug(f"DB_PATH: {db_path}")
        logger.debug(f"DATA_KEY: {data_key}")
        logger.debug(f"BACKUP_PATH: {backup_path}")

        # Check if any required variables are missing
        if not db_path or not data_key:
            logger.error("Required environment variables (DB_PATH, DATA_KEY) are not set.")
            sys.exit(1)

        # Initialize the database
        logger.info("Initializing database...")
        initialize_database(db_path, data_key)  # Pass db_path and data_key

        # Set up cloud integrations
        logger.info("Setting up cloud integrations...")
        
        # Adjusted integration setup calls with individual error handling
        try:
            if hasattr(AWSIntegration, 'initialize'):
                AWSIntegration.initialize()
            else:
                logger.error("AWSIntegration does not have an 'initialize' method.")
        except Exception as e:
            logger.error(f"Error initializing AWSIntegration: {e}")

        try:
            if hasattr(GCPIntegration, 'initialize'):
                GCPIntegration.initialize()
            else:
                logger.error("GCPIntegration does not have an 'initialize' method.")
        except Exception as e:
            logger.error(f"Error initializing GCPIntegration: {e}")

        try:
            if hasattr(AzureIntegration, 'initialize'):
                AzureIntegration.initialize()
            else:
                logger.error("AzureIntegration does not have an 'initialize' method.")
        except Exception as e:
            logger.error(f"Error initializing AzureIntegration: {e}")

        # Initialize monitoring tools with error handling for each tool
        logger.info("Initializing monitoring tools...")
        try:
            CPUUsage.start_monitoring()
        except Exception as e:
            logger.error(f"Failed to start CPU usage monitoring: {e}")

        try:
            AnalyticsDashboard.initialize()
        except Exception as e:
            logger.error(f"Failed to initialize Analytics Dashboard: {e}")

        # Load AI learning models
        logger.info("Loading AI learning module...")
        try:
            AILearning.load_models()
        except Exception as e:
            logger.error(f"Failed to load AI learning models: {e}")

        # Initialize system control module
        logger.info("Initializing system control module...")
        try:
            SystemControl.initialize()
        except Exception as e:
            logger.error(f"Failed to initialize system control module: {e}")

        logger.info("System initialization complete.")
    
    except Exception as e:
        logger.error(f"Error during initialization: {e}")
        sys.exit(1)

def main():
    """Main function to run Devin's AI assistant."""
    logger.info("Starting Devin AI assistant...")

    # Initialize services
    initialize_services()

    # Load modules
    voice_assistant = VoiceAssistant()
    gesture_recognition = GestureRecognition()
    nlp_conversation = NLPConversation()

    # Main event loop
    try:
        while True:
            logger.info("Listening for user input...")

            # Voice assistant activation
            if voice_assistant.detect_wake_word():
                command = voice_assistant.listen_and_transcribe()
                logger.debug(f"User command: {command}")

                if "exit" in command.lower():
                    logger.info("Exiting Devin AI assistant.")
                    break

                response = nlp_conversation.process_command(command)
                logger.debug(f"Response: {response}")
                voice_assistant.speak(response)

            # Gesture recognition activation
            if gesture_recognition.detect_gesture():
                logger.info("Gesture recognized. Executing corresponding action.")
                gesture_recognition.execute_action()

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt detected. Exiting Devin AI assistant.")
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
    finally:
        logger.info("Devin AI assistant shut down cleanly.")

if __name__ == "__main__":
    main()
