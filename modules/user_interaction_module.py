# Devin/modules/user_interaction_module.py
# Purpose: The central module for handling all text and voice-based interaction
#          between the AGI and the human operator.

import logging
import sys
import os
from typing import Optional

# Try to import speech recognition
try:
    from modules.multimedia_tools.speech_recognition import LiveSpeechRecognizer
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False

# Configure basic logging
logger = logging.getLogger("UserInteractionManager")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)
logger.propagate = False

# --- ANSI Color Codes for Formatted Output ---
class Colors:
    """Container for ANSI color codes."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class UserInteractionManager:
    """
    Manages all console I/O, providing a clear and secure interface
    for the user to interact with the AGI.
    """
    def __init__(self, use_voice: bool = False):
        self.use_voice = use_voice
        self.recognizer: Optional[LiveSpeechRecognizer] = None
        if self.use_voice:
            if SPEECH_AVAILABLE:
                try:
                    self.recognizer = LiveSpeechRecognizer()
                    logger.info("Voice input enabled.")
                except Exception as e:
                    logger.error(f"Failed to initialize voice recognizer: {e}")
                    self.use_voice = False
            else:
                logger.warning("Speech recognition dependencies not found. Falling back to text.")
                self.use_voice = False

    def get_user_input(self, prompt: str) -> str:
        """
        Prompts the user for general input (text or voice).
        """
        if self.use_voice and self.recognizer:
            print(f"{Colors.OKCYAN}{Colors.BOLD}[VOICE PROMPT] {prompt}{Colors.ENDC}")
            print(f"{Colors.HEADER}Listening... (Press Ctrl+C to switch to text){Colors.ENDC}")
            try:
                text = self.recognizer.listen_and_transcribe(engine='google')
                if text:
                    print(f"{Colors.OKGREEN}[YOU SAID] {text}{Colors.ENDC}")
                    return text.strip()
                else:
                    print(f"{Colors.WARNING}No speech detected. Falling back to text input.{Colors.ENDC}")
            except KeyboardInterrupt:
                print(f"\n{Colors.WARNING}Voice input interrupted. Switching to text for this prompt.{Colors.ENDC}")
            except Exception as e:
                logger.error(f"Error during voice input: {e}")

        try:
            # Use a distinct color for user prompts
            full_prompt = f"{Colors.OKCYAN}{Colors.BOLD}[PROMPT] {prompt}{Colors.ENDC} "
            response = input(full_prompt)
            return response.strip()
        except KeyboardInterrupt:
            logger.warning("\nUser interrupted input. Returning empty string.")
            return ""

    def ask_for_confirmation(self, prompt: str, is_dangerous: bool = False) -> bool:
        """
        Asks the user a yes/no question and returns a boolean.
        """
        if is_dangerous:
            warning_header = f"{Colors.FAIL}{Colors.BOLD}{'='*60}\n"
            warning_header += "!!! DANGEROUS ACTION REQUIRES CONFIRMATION !!!\n"
            warning_header += f"{'='*60}{Colors.ENDC}"
            
            full_prompt = f"\n{warning_header}\n{Colors.WARNING}{prompt}{Colors.ENDC}\n"
            prompt_suffix = f"{Colors.BOLD}Are you absolutely sure you want to proceed? (yes/no):{Colors.ENDC} "
        else:
            full_prompt = f"{Colors.WARNING}[CONFIRM] {prompt}{Colors.ENDC}"
            prompt_suffix = " (y/n): "

        try:
            response = input(full_prompt + prompt_suffix).lower().strip()
            if response in ['y', 'yes']:
                return True
            else:
                return False
        except KeyboardInterrupt:
            logger.warning("\nUser interrupted confirmation. Defaulting to NO.")
            return False

    def display_message(self, message: str, level: str = 'info'):
        """Displays a formatted message to the user."""
        if level == 'info':
            print(f"{Colors.OKBLUE}[INFO] {message}{Colors.ENDC}")
        elif level == 'success':
            print(f"{Colors.OKGREEN}[SUCCESS] {message}{Colors.ENDC}")
        elif level == 'warning':
            print(f"{Colors.WARNING}[WARNING] {message}{Colors.ENDC}")
        elif level == 'error':
            print(f"{Colors.FAIL}[ERROR] {message}{Colors.ENDC}")
        else:
            print(message)
