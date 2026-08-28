# bootstrap.py
"""
Initializes all services, AI models, and dependencies for the Devin project.
This script sets up core functionalities and ensures smooth integration between modules.
"""

import os
import sys
import logging
import importlib
from pathlib import Path
from dotenv import load_dotenv

# Logger configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DevinBootstrap")

def load_environment_variables():
    """Load environment variables from .env file."""
    dotenv_path = Path(".env")
    if dotenv_path.exists():
        load_dotenv(dotenv_path)
        logger.info("Environment variables loaded from .env file.")
    else:
        logger.warning(".env file not found. Ensure environment variables are set.")

def initialize_dependencies():
    """Ensure all required dependencies are installed."""
    logger.info("Checking and installing required dependencies...")
    try:
        import pip
        requirements_path = Path("requirements.txt")
        if requirements_path.exists():
            os.system(f"{sys.executable} -m pip install -r {requirements_path}")
            logger.info("All dependencies installed successfully.")
        else:
            logger.warning("requirements.txt not found. Skipping dependency installation.")
    except Exception as e:
        logger.error(f"Error installing dependencies: {e}")

def load_services():
    """Dynamically load all services from the services/ directory."""
    services_dir = Path("services/")
    if services_dir.exists():
        sys.path.append(str(services_dir))
        for service_file in services_dir.glob("*.py"):
            module_name = service_file.stem
            try:
                importlib.import_module(module_name)
                logger.info(f"Service '{module_name}' loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load service '{module_name}': {e}")
    else:
        logger.warning("No services directory found. Ensure services are correctly set up.")

def initialize_ai_models():
    """Load and initialize AI models."""
    logger.info("Initializing AI models...")
    ai_models_dir = Path("ai_models/")
    if ai_models_dir.exists():
        sys.path.append(str(ai_models_dir))
        for model_file in ai_models_dir.glob("*.py"):
            module_name = model_file.stem
            try:
                model_module = importlib.import_module(module_name)
                if hasattr(model_module, "initialize_model"):
                    model_module.initialize_model()
                logger.info(f"AI Model '{module_name}' initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize AI Model '{module_name}': {e}")
    else:
        logger.warning("No AI models directory found. Ensure AI models are correctly set up.")

def start_services():
    """Start essential services for the Devin project."""
    logger.info("Starting essential services...")
    try:
        from services.core_service import start_core_service
        start_core_service()
    except ImportError:
        logger.warning("Core service not found. Ensure it is implemented.")

def bootstrap():
    """Main bootstrap process for the Devin project."""
    logger.info("Starting bootstrap process...")
    load_environment_variables()
    initialize_dependencies()
    load_services()
    initialize_ai_models()
    start_services()
    logger.info("Bootstrap process completed successfully. Devin is ready.")

if __name__ == "__main__":
    bootstrap()
