# Devin/plugins/voice_assistant.py
# Purpose: An all-in-one, voice-driven assistant that integrates speech
#          recognition, the AI chatbot engine, and text-to-speech.

import logging
import os
import sys
from pathlib import Path
import tempfile

# --- Prerequisite library for audio playback ---
try:
    import simpleaudio as sa
    SIMPLEAUDIO_AVAILABLE = True
except ImportError:
    SIMPLEAUDIO_AVAILABLE = False

# --- Import other Devin modules ---
try:
    from modules.multimedia_tools.speech_recognition import LiveSpeechRecognizer
    from modules.multimedia_tools.audio_processing import AudioProcessor
    from modules.ai_tools.chatbot_engine import ChatbotEngine
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# Configure basic logging
logger = logging.getLogger("VoiceAssistant")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False

class VoiceAssistant:
    """
    Orchestrates a full voice-in, voice-out conversational loop.
    """
    def __init__(self, openai_api_key: Optional[str] = None):
        if not DEVIN_CORE_AVAILABLE:
            raise ImportError(f"Could not import a core Devin module. Ensure all tools are present. Error: {_import_error}")
        if not SIMPLEAUDIO_AVAILABLE:
            raise ImportError("SimpleAudio is required for audio playback. 'pip install simpleaudio'")

        self.speech_recognizer = LiveSpeechRecognizer(openai_api_key)
        self.chatbot_engine = ChatbotEngine(openai_api_key)
        self.audio_processor = AudioProcessor() # Static methods are used, but instantiation is good practice.

    def _speak(self, text: str):
        """Converts text to speech and plays it."""
        logger.info(f"Speaking: '{text}'")
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                tmp_path = Path(tmp_file.name)
            
            success = self.audio_processor.text_to_speech(text, tmp_path)
            if success:
                wave_obj = sa.WaveObject.from_wave_file(str(tmp_path))
                play_obj = wave_obj.play()
                play_obj.wait_done()
        except Exception as e:
            logger.error(f"Failed to speak text: {e}")
        finally:
            if 'tmp_path' in locals() and tmp_path.exists():
                tmp_path.unlink()

    def start_conversation_loop(self):
        """Initiates the main interactive loop for the voice assistant."""
        self._speak("Devin voice assistant activated. How can I assist you?")
        
        while True:
            try:
                input("\nPress Enter to speak to Devin (or Ctrl+C to exit)...")
                
                # 1. Listen for user's command
                user_text = self.speech_recognizer.listen_and_transcribe(engine='google')
                
                if not user_text:
                    continue # Listen again if nothing was heard
                
                logger.info(f"User said: '{user_text}'")
                
                if user_text.lower().strip() in ['exit', 'quit', 'stop', 'goodbye']:
                    self._speak("Goodbye.")
                    break

                # 2. Process the command with the AI brain
                responses = self.chatbot_engine.process_user_message(user_text)

                # 3. Handle the AI's response (speak or narrate action)
                for response in responses:
                    if response.get("type") == "text":
                        self._speak(response.get("content", "I have no response."))
                    
                    elif response.get("type") == "tool_call":
                        # For a tool call, we narrate the action
                        tool_name = response.get("function_name", "an unknown tool")
                        narration = f"Understood. Executing the tool: {tool_name.replace('_', ' ')}."
                        self._speak(narration)
                        # In the final app, this is where the tool would actually be executed.
                        # For this demo, we just print the action.
                        logger.info("--- [ACTION WOULD BE EXECUTED HERE] ---")
                        logger.info(f"Tool: {tool_name}")
                        logger.info(f"Parameters: {response.get('arguments')}")
                        logger.info("------------------------------------")

            except (KeyboardInterrupt, EOFError):
                self._speak("Voice assistant shutting down.")
                break

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Devin Voice Assistant Prototype 🗣️🤖 ===")
    print("=========================================================")
    
    # Check for all dependencies first
    if not DEVIN_CORE_AVAILABLE:
        print(f"\nERROR: A core Devin module could not be imported. Please ensure all project files are in place. Error: {_import_error}")
        sys.exit(1)
    if not SIMPLEAUDIO_AVAILABLE:
        print("\nERROR: Missing required library. Please run: 'pip install simpleaudio'")
        sys.exit(1)
    if not os.getenv("OPENAI_API_KEY"):
         print("\nERROR: OPENAI_API_KEY environment variable is not set. This demo requires it for the chatbot and TTS.")
         sys.exit(1)

    try:
        assistant = VoiceAssistant()
        assistant.start_conversation_loop()
    except Exception as e:
        logger.error(f"Failed to start the Voice Assistant: {e}")
    
    print("\n=========================================================")
    print("=== Voice Assistant Prototype Complete ===")
    print("=========================================================")
