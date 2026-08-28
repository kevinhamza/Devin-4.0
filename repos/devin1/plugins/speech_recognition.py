"""
speech_recognition.py
----------------------
Provides advanced speech recognition and translation functionalities.
Supports multiple languages and real-time transcription and translation.
"""

import speech_recognition as sr
from googletrans import Translator


class SpeechRecognition:
    def __init__(self, audio_file: str = None):
        self.audio_file = audio_file
        self.recognizer = sr.Recognizer()
        self.translator = Translator()

    def recognize_speech(self, language: str = 'en-US'):
        """Transcribes speech from an audio file."""
        if not self.audio_file or not os.path.exists(self.audio_file):
            raise FileNotFoundError(f"Audio file '{self.audio_file}' not found.")
        try:
            with sr.AudioFile(self.audio_file) as source:
                audio_data = self.recognizer.record(source)
                transcription = self.recognizer.recognize_google(audio_data, language=language)
                return transcription
        except Exception as e:
            raise RuntimeError(f"Error during speech recognition: {e}")

    def recognize_realtime_speech(self, language: str = 'en-US'):
        """Recognizes speech in real-time from the microphone."""
        try:
            with sr.Microphone() as source:
                print("Please speak...")
                audio_data = self.recognizer.listen(source)
                transcription = self.recognizer.recognize_google(audio_data, language=language)
                return transcription
        except Exception as e:
            raise RuntimeError(f"Error during real-time speech recognition: {e}")

    def translate_text(self, text: str, target_language: str = 'en'):
        """Translates text to the specified target language."""
        try:
            translation = self.translator.translate(text, dest=target_language)
            return translation.text
        except Exception as e:
            raise RuntimeError(f"Error during translation: {e}")

    def recognize_and_translate(self, target_language: str = 'en', input_language: str = 'auto'):
        """Recognizes speech and translates it to the target language."""
        transcription = self.recognize_speech(language=input_language)
        translation = self.translate_text(transcription, target_language)
        return {"transcription": transcription, "translation": translation}


# Example Usage
if __name__ == "__main__":
    audio_file = "example_audio.wav"
    speech_recognizer = SpeechRecognition(audio_file)

    # Recognize speech from a file
    transcription = speech_recognizer.recognize_speech(language="en-US")
    print(f"Transcription: {transcription}")

    # Real-time speech recognition
    try:
        live_transcription = speech_recognizer.recognize_realtime_speech(language="en-US")
        print(f"Real-Time Transcription: {live_transcription}")
    except RuntimeError as e:
        print(e)

    # Translate recognized text
    translation = speech_recognizer.translate_text("Hola, ¿cómo estás?", target_language="en")
    print(f"Translation: {translation}")

    # Recognize and translate
    recognized_translated = speech_recognizer.recognize_and_translate(target_language="fr")
    print(f"Recognized Text: {recognized_translated['transcription']}")
    print(f"Translated Text: {recognized_translated['translation']}")
