"""
Speech Recognition and Translation Tools
========================================
This module provides tools for recognizing speech from audio files or live input 
and translating the recognized text into various languages. 

Dependencies:
- SpeechRecognition for speech-to-text
- googletrans for text translation
- pyttsx3 for text-to-speech
"""

import speech_recognition as sr
from googletrans import Translator
import pyttsx3


class SpeechRecognitionAndTranslation:
    """
    A class for speech recognition and translation functionalities.
    """

    def __init__(self):
        """
        Initializes the SpeechRecognitionAndTranslation class.
        """
        self.recognizer = sr.Recognizer()
        self.translator = Translator()
        self.tts_engine = pyttsx3.init()

    # -----------------------
    # Speech Recognition
    # -----------------------

    def recognize_speech_from_audio(self, audio_file):
        """
        Recognizes speech from an audio file.

        Args:
            audio_file (str): Path to the audio file.

        Returns:
            str: Recognized text from the audio.
        """
        try:
            with sr.AudioFile(audio_file) as source:
                print("Listening to the audio file...")
                audio_data = self.recognizer.record(source)
                recognized_text = self.recognizer.recognize_google(audio_data)
                return recognized_text
        except Exception as e:
            return f"Error recognizing speech: {e}"

    def recognize_speech_from_microphone(self):
        """
        Recognizes speech from the microphone in real time.

        Returns:
            str: Recognized text from the speech.
        """
        try:
            with sr.Microphone() as source:
                print("Adjusting for ambient noise... Speak now!")
                self.recognizer.adjust_for_ambient_noise(source)
                audio_data = self.recognizer.listen(source)
                recognized_text = self.recognizer.recognize_google(audio_data)
                return recognized_text
        except Exception as e:
            return f"Error recognizing speech: {e}"

    # -----------------------
    # Translation
    # -----------------------

    def translate_text(self, text, target_language='en'):
        """
        Translates text into a target language.

        Args:
            text (str): The text to translate.
            target_language (str): Language code of the target language (e.g., 'en' for English).

        Returns:
            str: Translated text.
        """
        try:
            translated_text = self.translator.translate(text, dest=target_language).text
            return translated_text
        except Exception as e:
            return f"Error translating text: {e}"

    # -----------------------
    # Text-to-Speech (TTS)
    # -----------------------

    def text_to_speech(self, text, language='en'):
        """
        Converts text to speech in a specified language.

        Args:
            text (str): The text to convert.
            language (str): Language code for the TTS (e.g., 'en' for English).

        Returns:
            None
        """
        try:
            self.tts_engine.setProperty('voice', self._get_voice_by_language(language))
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"Error during text-to-speech: {e}")

    def _get_voice_by_language(self, language):
        """
        Returns a suitable voice ID for the given language.

        Args:
            language (str): Language code.

        Returns:
            str: Voice ID.
        """
        voices = self.tts_engine.getProperty('voices')
        for voice in voices:
            if language in voice.languages:
                return voice.id
        return voices[0].id  # Fallback to the default voice

    # -----------------------
    # Combined Features
    # -----------------------

    def recognize_and_translate(self, audio_file, target_language='en'):
        """
        Recognizes speech from an audio file and translates the text into a target language.

        Args:
            audio_file (str): Path to the audio file.
            target_language (str): Language code for translation.

        Returns:
            str: Translated text.
        """
        recognized_text = self.recognize_speech_from_audio(audio_file)
        if "Error" in recognized_text:
            return recognized_text
        translated_text = self.translate_text(recognized_text, target_language)
        return translated_text

    def live_recognition_and_translation(self, target_language='en'):
        """
        Performs live speech recognition and translates the recognized text into a target language.

        Args:
            target_language (str): Language code for translation.

        Returns:
            str: Translated text.
        """
        recognized_text = self.recognize_speech_from_microphone()
        if "Error" in recognized_text:
            return recognized_text
        translated_text = self.translate_text(recognized_text, target_language)
        return translated_text


# Example Usage
if __name__ == "__main__":
    srt = SpeechRecognitionAndTranslation()

    # Recognize speech from an audio file
    audio_file = "example.wav"
    print("Recognized Speech:", srt.recognize_speech_from_audio(audio_file))

    # Translate text to French
    text = "Hello, how are you?"
    print("Translated Text:", srt.translate_text(text, target_language='fr'))

    # Recognize speech and translate to Spanish
    print("Recognized and Translated Speech:", srt.recognize_and_translate(audio_file, target_language='es'))

    # Live recognition and translation to German
    print("Live Translation:", srt.live_recognition_and_translation(target_language='de'))

    # Convert text to speech in Spanish
    srt.text_to_speech("Hola, ¿cómo estás?", language='es')
