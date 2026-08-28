# Devin/tests/integration/test_nlp_conversation.py
# Purpose: An end-to-end integration test for the full conversational loop,
#          verifying that the STT, NLP, and TTS modules can be orchestrated
#          by the VoiceAssistant to handle a multi-turn dialogue.

import unittest
from unittest.mock import patch, MagicMock, call

# --- Important: We need to set up the path to import our modules ---
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

try:
    from modules.robotics.voice_assistant import VoiceAssistant
    from modules.robotics.speech_to_text import SpeechToText
    from modules.robotics.text_to_speech import TextToSpeech
    from modules.robotics.natural_language_processing import NLPProcessor, Intent
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# --- Suppress regular logging output during tests for clarity ---
import logging
logging.disable(logging.CRITICAL)


# --- A more advanced VoiceAssistant with conversational memory for testing ---
class ConversationalVoiceAssistant(VoiceAssistant):
    """An enhanced VoiceAssistant that can handle simple, multi-turn conversations."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conversation_context = {}

    def _process_command(self, command: str):
        # Check if we are waiting for a piece of information
        if self.conversation_context.get("waiting_for_entity"):
            # Try to merge the new information with the old command
            previous_command = self.conversation_context.get("previous_command")
            full_command_text = f"{previous_command.original_text} {command}"
            structured_command = self.nlp.process_command(full_command_text)
            self.conversation_context.clear() # Clear context after using it
        else:
            structured_command = self.nlp.process_command(command)

        if not structured_command:
            self.speak("I'm sorry, I had trouble processing that.")
            return

        # Check if the command is complete
        if structured_command.intent == Intent.FIND_OBJECT and "object" in structured_command.entities and "color" not in structured_command.entities:
            # Command is incomplete, ask a clarifying question
            self.speak(f"I can look for the {structured_command.entities['object']}. What color is it?")
            self.conversation_context["waiting_for_entity"] = "color"
            self.conversation_context["previous_command"] = structured_command
        elif structured_command.intent == Intent.FIND_OBJECT:
            obj = structured_command.entities.get('object', 'item')
            color = structured_command.entities.get('color', '')
            self.speak(f"Okay, I will now look for the {color} {obj}.")
        else:
            self.speak(f"I understood the command: {command}")


@unittest.skipUnless(DEVIN_CORE_AVAILABLE, f"Skipping integration tests, dependency missing: {_import_error}")
class TestEndToEndConversation(unittest.TestCase):
    """
    Tests the full "Listen -> Think -> Speak" loop for a multi-turn conversation.
    """

    @patch('modules.robotics.speech_to_text.sr.Recognizer')
    @patch('modules.robotics.speech_to_text.sr.Microphone')
    @patch('modules.robotics.text_to_speech.pyttsx3.init')
    def test_e2e_clarification_dialogue(self, mock_tts_init, mock_mic, mock_recognizer):
        """
        Verify the full conversational chain:
        1. User gives an incomplete command.
        2. Assistant asks a clarifying question.
        3. User provides the missing info.
        4. Assistant confirms the complete command.
        """
        print("\n\n--- Testing E2E Multi-Turn Conversational Workflow ---")

        # --- 1. Setup Mocks ---
        # Mock the TTS engine to capture what the assistant says
        mock_tts_engine = MagicMock()
        mock_tts_init.return_value = mock_tts_engine

        # Mock the STT engine to simulate a user speaking a sequence of phrases
        mock_recognizer_instance = mock_recognizer.return_value
        mock_recognizer_instance.recognize_google.side_effect = [
            "devin find the ball", # User's first command
            "the red one",         # User's answer to the clarifying question
        ]
        
        # --- 2. Instantiate REAL modules ---
        # The low-level speech libraries are mocked, but our wrapper classes are real.
        s_to_t = SpeechToText()
        t_to_s = TextToSpeech()
        nlp = NLPProcessor()
        
        # We inject our real (but internally mocked) modules into our advanced assistant
        assistant = ConversationalVoiceAssistant(wake_word="devin")
        assistant.stt = s_to_t
        assistant.tts = t_to_s
        assistant.nlp = nlp

        # --- 3. Simulate the Conversation ---
        print("  [Turn 1] Simulating user's initial, incomplete command...")
        # This is the entry point for the background listener
        assistant._handle_background_speech("devin find the ball")

        print("  [Turn 2] Simulating user's clarifying response...")
        assistant._handle_background_speech("the red one")
        
        # --- 4. Verify the Full Conversation ---
        # Check the sequence of things the assistant SAID
        spoken_phrases = [args[0] for args, kwargs in mock_tts_engine.say.call_args_list]
        
        # Expected conversation flow from the assistant:
        # 1. Acknowledge the wake word
        self.assertIn("Yes?", spoken_phrases[0])
        print("  [SUCCESS] Assistant correctly acknowledged the wake word.")
        
        # 2. Ask the clarifying question
        self.assertIn("What color is it?", spoken_phrases[1])
        print("  [SUCCESS] Assistant correctly asked for the missing color.")
        
        # 3. Confirm the final, complete command
        self.assertIn("Okay, I will now look for the red ball", spoken_phrases[2])
        print("  [SUCCESS] Assistant correctly confirmed the final, complete command.")


if __name__ == '__main__':
    unittest.main()
