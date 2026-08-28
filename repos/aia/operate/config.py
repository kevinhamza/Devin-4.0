import os
import logging
from dotenv import load_dotenv
from pathlib import Path


class Config:
    """
    Handles loading and managing configuration settings, including API keys,
    system paths, and other environment variables required for the operation of the system.
    """

    def __init__(self):
        # Load environment variables from the .env file
        load_dotenv(dotenv_path=Path('.') / '.env')
        self.logger = logging.getLogger("Config")
        self.logger.setLevel(logging.DEBUG)

        # API Keys and configurations
        self.api_keys = self._load_api_keys()

        # Other configurations
        self.model_config = self._load_model_config()

    def _load_api_keys(self) -> dict[str, str]:
        """Load API keys from environment variables."""
        try:
            api_keys = {
                'openai_key': os.getenv('OPENAI_API_KEY', ''),
                'google_api_key': os.getenv('GOOGLE_API_KEY', ''),
                'whiterabbit_api_key': os.getenv('WHITERABBIT_API_KEY', ''),
                'twitter_api_key': os.getenv('TWITTER_API_KEY', ''),
            }

            # Log warnings for missing API keys
            for key, value in api_keys.items():
                if not value:
                    self.logger.warning(f"API key for {key} is missing or empty.")
            return api_keys
        except Exception as e:
            self.logger.error(f"Failed to load API keys: {e}")
            return {}

    def _load_model_config(self) -> dict[str, str]:
        """Load model-specific configurations (e.g., model paths, settings)."""
        try:
            model_config = {
                'language_model': os.getenv('LANGUAGE_MODEL', 'gpt-3.5-turbo'),
                'image_model': os.getenv('IMAGE_MODEL', 'dall-e-2'),
                'voice_model': os.getenv('VOICE_MODEL', 'whisper'),
                'default_model_type': os.getenv('MODEL_TYPE', 'random_forest'),
            }
            self.logger.debug(f"Model configurations loaded: {model_config}")
            return model_config
        except Exception as e:
            self.logger.error(f"Failed to load model configuration: {e}")
            return {}

    def get_api_key(self, key_name: str) -> str:
        """Retrieve a specific API key."""
        return self.api_keys.get(key_name, '')

    def get_model_config(self, key_name: str) -> str:
        """Retrieve a specific model configuration."""
        return self.model_config.get(key_name, '')

    def save_config(self, config_data: dict[str, str]) -> bool:
        """Save updated configurations to the .env file."""
        try:
            with open('.env', 'a') as f:
                for key, value in config_data.items():
                    f.write(f'{key}={value}\n')
            self.logger.info("Configuration saved successfully.")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False

    def reload_config(self) -> bool:
        """Reload configuration settings from the .env file."""
        try:
            load_dotenv(dotenv_path=Path('.') / '.env', override=True)
            self.logger.info("Configuration reloaded successfully.")
            return True
        except Exception as e:
            self.logger.error(f"Failed to reload configuration: {e}")
            return False

    def print_config(self) -> None:
        """Print out the current configuration settings."""
        try:
            print("API Keys:")
            for key, value in self.api_keys.items():
                print(f"{key}: {value or 'Not Set'}")
            print("\nModel Configurations:")
            for key, value in self.model_config.items():
                print(f"{key}: {value or 'Not Set'}")
        except Exception as e:
            self.logger.error(f"Failed to print configuration: {e}")


def load_config() -> Config:
    """
    A function to create and return a Config instance.
    This is used for initializing configuration in other parts of the system.
    """
    return Config()


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    config = load_config()

    # Load and print current configuration
    config.print_config()

    # Get specific API key
    openai_key = config.get_api_key('openai_key')
    print(f"OpenAI API Key: {openai_key}")

    # Save new configuration
    new_config = {'NEW_API_KEY': '12345'}
    config.save_config(new_config)

    # Reload configuration
    config.reload_config()
