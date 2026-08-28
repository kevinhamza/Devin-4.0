"""
modules/voice.py — Cross-platform voice I/O for Devin AGI
TTS via pyttsx3, STT via SpeechRecognition, wake-word detection.
Gracefully degrades if audio hardware is unavailable.
"""

import threading
import time
import os

# ── TTS ───────────────────────────────────────────────────────────────────────

try:
    import pyttsx3 as _pyttsx3
    _tts_engine = _pyttsx3.init()
    _tts_engine.setProperty('rate', 170)
    _tts_engine.setProperty('volume', 0.95)
    HAS_TTS = True
except Exception:
    HAS_TTS = False
    _tts_engine = None

# ── STT ───────────────────────────────────────────────────────────────────────

try:
    import speech_recognition as _sr
    _recognizer = _sr.Recognizer()
    _recognizer.energy_threshold = 300
    _recognizer.dynamic_energy_threshold = True
    HAS_STT = True
except Exception:
    HAS_STT = False
    _sr = None
    _recognizer = None

# ── Whisper fallback ──────────────────────────────────────────────────────────

try:
    import whisper as _whisper
    HAS_WHISPER = True
except Exception:
    HAS_WHISPER = False
    _whisper = None


def speak(text: str, rate: int = 170, volume: float = 0.95) -> bool:
    """Speak text aloud. Returns True on success."""
    if not text:
        return False
    # Try pyttsx3
    if HAS_TTS and _tts_engine:
        try:
            _tts_engine.setProperty('rate', rate)
            _tts_engine.setProperty('volume', volume)
            _tts_engine.say(str(text))
            _tts_engine.runAndWait()
            return True
        except Exception:
            pass
    # Try espeak fallback
    try:
        import subprocess
        subprocess.run(['espeak', str(text)[:500]], capture_output=True, timeout=10)
        return True
    except Exception:
        pass
    return False


def listen(timeout: int = 8, phrase_limit: int = 15, language: str = 'en-US') -> str:
    """Listen for speech, return transcribed text or empty string."""
    if not HAS_STT or _recognizer is None:
        return ''
    try:
        with _sr.Microphone() as source:
            _recognizer.adjust_for_ambient_noise(source, duration=0.4)
            print('\033[36m  ◉ Listening…\033[0m', flush=True)
            try:
                audio = _recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
            except _sr.WaitTimeoutError:
                return ''

        # Google STT
        try:
            return _recognizer.recognize_google(audio, language=language).strip()
        except _sr.UnknownValueError:
            return ''
        except _sr.RequestError:
            pass

        # Whisper fallback
        if HAS_WHISPER:
            try:
                import tempfile
                tmp = tempfile.mktemp(suffix='.wav')
                with open(tmp, 'wb') as f:
                    f.write(audio.get_wav_data())
                model = _whisper.load_model('tiny')
                result = model.transcribe(tmp)
                os.remove(tmp)
                return result.get('text', '').strip()
            except Exception:
                pass
    except Exception:
        pass
    return ''


def listen_for_wake_word(wake_word: str = 'devin', timeout_each: int = 10) -> str:
    """
    Continuously listen until wake word is detected.
    Returns the full utterance that contained the wake word.
    Blocks the calling thread.
    """
    if not HAS_STT:
        return ''
    while True:
        try:
            text = listen(timeout=timeout_each, phrase_limit=8)
            if text and wake_word.lower() in text.lower():
                return text
        except Exception:
            time.sleep(0.5)


class VoiceThread:
    """Background wake-word listener. Calls callback(utterance) when triggered."""

    def __init__(self, callback, wake_word: str = 'devin'):
        self.callback = callback
        self.wake_word = wake_word
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def start(self):
        if HAS_STT:
            self._thread.start()

    def stop(self):
        self._stop.set()

    def _loop(self):
        while not self._stop.is_set():
            text = listen(timeout=10, phrase_limit=8)
            if text and self.wake_word.lower() in text.lower():
                try:
                    self.callback(text)
                except Exception:
                    pass
