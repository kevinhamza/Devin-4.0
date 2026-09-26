"""
voice_control.py — Enhanced voice input/output for Devin.
Supports: pyttsx3 (offline), gTTS (Google), system TTS (espeak/say),
          SpeechRecognition (Google STT), Whisper (local STT).
Auto-detects the best available backend.
"""
from __future__ import annotations

import os
import sys
import threading
import queue
import tempfile
from typing import Optional, Callable

_TTS_BACKEND = os.environ.get('DEVIN_TTS_BACKEND', 'auto').lower()
_STT_BACKEND = os.environ.get('DEVIN_STT_BACKEND', 'auto').lower()
_LANG = os.environ.get('DEVIN_VOICE_LANG', 'en')


# ── TTS (text-to-speech) ──────────────────────────────────────────────────────

class TTSEngine:
    """Unified text-to-speech interface."""

    def __init__(self, backend: str = 'auto'):
        self.backend = backend
        self._engine = None
        self._init_backend()

    def _init_backend(self):
        b = self.backend
        if b in ('auto', 'pyttsx3'):
            try:
                import pyttsx3
                self._engine = pyttsx3.init()
                self._engine.setProperty('rate', 185)
                self._engine.setProperty('volume', 0.9)
                self.backend = 'pyttsx3'
                return
            except Exception:
                if b == 'pyttsx3':
                    raise
        if b in ('auto', 'gtts'):
            try:
                from gtts import gTTS
                # Quick test
                self.backend = 'gtts'
                return
            except ImportError:
                if b == 'gtts':
                    raise
        if b in ('auto', 'system'):
            import shutil
            for cmd in ['espeak', 'say', 'spd-say']:
                if shutil.which(cmd):
                    self._engine = cmd
                    self.backend = 'system'
                    return
        self.backend = 'none'

    def speak(self, text: str, block: bool = True) -> None:
        """Speak text aloud."""
        if self.backend == 'none' or not text.strip():
            return
        if self.backend == 'pyttsx3':
            self._engine.say(text)
            if block:
                self._engine.runAndWait()
            else:
                threading.Thread(target=self._engine.runAndWait, daemon=True).start()
        elif self.backend == 'gtts':
            self._speak_gtts(text, block)
        elif self.backend == 'system':
            self._speak_system(text, block)

    def _speak_gtts(self, text: str, block: bool) -> None:
        import subprocess
        from gtts import gTTS
        try:
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                fname = f.name
            gTTS(text=text[:500], lang=_LANG).save(fname)
            players = ['mpg123', 'mpg321', 'mplayer', 'ffplay', 'play']
            import shutil
            for p in players:
                if shutil.which(p):
                    cmd = [p, '-q', fname] if p in ('mpg123', 'mpg321') else [p, fname]
                    if block:
                        subprocess.run(cmd, capture_output=True)
                    else:
                        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return
        except Exception:
            pass
        finally:
            try:
                os.unlink(fname)
            except Exception:
                pass

    def _speak_system(self, text: str, block: bool) -> None:
        import subprocess
        cmd = self._engine
        if cmd == 'espeak':
            args = ['espeak', '-v', _LANG, text[:500]]
        elif cmd == 'say':  # macOS
            args = ['say', text[:500]]
        elif cmd == 'spd-say':
            args = ['spd-say', text[:500]]
        else:
            return
        if block:
            subprocess.run(args, capture_output=True)
        else:
            subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def stop(self) -> None:
        if self.backend == 'pyttsx3' and self._engine:
            try:
                self._engine.stop()
            except Exception:
                pass

    def is_available(self) -> bool:
        return self.backend != 'none'

    def __repr__(self):
        return f'TTSEngine(backend={self.backend!r})'


# ── STT (speech-to-text) ─────────────────────────────────────────────────────

class STTEngine:
    """Unified speech-to-text interface."""

    def __init__(self, backend: str = 'auto'):
        self.backend = backend
        self._init_backend()

    def _init_backend(self):
        b = self.backend
        if b in ('auto', 'whisper'):
            try:
                import whisper  # openai-whisper
                self.backend = 'whisper'
                self._model = None  # lazy load
                return
            except ImportError:
                if b == 'whisper':
                    raise
        if b in ('auto', 'google'):
            try:
                import speech_recognition
                self.backend = 'google'
                return
            except ImportError:
                if b == 'google':
                    raise
        self.backend = 'none'

    def listen(self, timeout: int = 8, phrase_limit: int = 30,
               on_partial: Optional[Callable[[str], None]] = None) -> Optional[str]:
        """Listen for voice input and return transcribed text."""
        if self.backend == 'none':
            return None
        if self.backend == 'google':
            return self._listen_google(timeout, phrase_limit)
        if self.backend == 'whisper':
            return self._listen_whisper(timeout, phrase_limit)
        return None

    def _listen_google(self, timeout: int, phrase_limit: int) -> Optional[str]:
        import speech_recognition as sr
        r = sr.Recognizer()
        r.energy_threshold = 300
        r.dynamic_energy_threshold = True
        r.pause_threshold = 0.8
        try:
            with sr.Microphone() as source:
                print('\033[2m  🎤 Listening…\033[0m', end='', flush=True)
                r.adjust_for_ambient_noise(source, duration=0.5)
                audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
            print('\r\033[2K', end='')
            text = r.recognize_google(audio, language=_LANG + '-' + _LANG.upper())
            return text
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except Exception:
            return None

    def _listen_whisper(self, timeout: int, phrase_limit: int) -> Optional[str]:
        try:
            import whisper
            import sounddevice as sd
            import numpy as np
            import soundfile as sf

            if self._model is None:
                self._model = whisper.load_model('base')

            sr = 16000
            print('\033[2m  🎤 Listening (Whisper)…\033[0m', end='', flush=True)
            audio = sd.rec(int(phrase_limit * sr), samplerate=sr, channels=1,
                           dtype='float32')
            sd.wait()
            print('\r\033[2K', end='')
            audio_np = audio.squeeze()
            result = self._model.transcribe(audio_np, language=_LANG, fp16=False)
            return result.get('text', '').strip() or None
        except Exception:
            return None

    def is_available(self) -> bool:
        return self.backend != 'none'

    def __repr__(self):
        return f'STTEngine(backend={self.backend!r})'


# ── Wake word detection (simple keyword-based) ───────────────────────────────

class WakeWordDetector:
    """Simple keyword-based wake word detector."""

    DEFAULT_WORDS = ['devin', 'hey devin', 'ok devin', 'devin wake']

    def __init__(self, wake_words: Optional[list] = None, stt: Optional[STTEngine] = None):
        self.wake_words = [w.lower() for w in (wake_words or self.DEFAULT_WORDS)]
        self.stt = stt or STTEngine()
        self._running = False
        self._callback: Optional[Callable[[str], None]] = None

    def _is_wake(self, text: str) -> bool:
        t = text.lower().strip()
        return any(w in t for w in self.wake_words)

    def start_background(self, callback: Callable[[str], None]) -> None:
        """Start listening for wake word in background. callback(user_text) is called."""
        self._callback = callback
        self._running = True
        threading.Thread(target=self._loop, daemon=True).start()

    def stop(self) -> None:
        self._running = False

    def _loop(self) -> None:
        while self._running:
            text = self.stt.listen(timeout=5, phrase_limit=6)
            if text and self._is_wake(text):
                # Strip wake word, pass remainder
                remainder = text
                for w in self.wake_words:
                    remainder = re.sub(re.escape(w), '', remainder, flags=re.IGNORECASE).strip(',. ')
                if self._callback:
                    self._callback(remainder or '')


# ── Voice session (high-level) ────────────────────────────────────────────────

class VoiceSession:
    """High-level voice interaction session combining TTS + STT."""

    def __init__(self, tts_backend: str = 'auto', stt_backend: str = 'auto'):
        self.tts = TTSEngine(backend=tts_backend)
        self.stt = STTEngine(backend=stt_backend)

    def greet(self) -> None:
        if self.tts.is_available():
            self.tts.speak("Hello! Devin is ready. How can I help you?", block=False)

    def listen_and_transcribe(self, timeout: int = 10) -> Optional[str]:
        return self.stt.listen(timeout=timeout)

    def speak_response(self, text: str, max_chars: int = 500) -> None:
        if not self.tts.is_available():
            return
        # Remove markdown formatting for speech
        import re
        clean = re.sub(r'```[\s\S]*?```', 'code block', text)
        clean = re.sub(r'`[^`]+`', lambda m: m.group(0).strip('`'), clean)
        clean = re.sub(r'\*\*(.+?)\*\*', r'\1', clean)
        clean = re.sub(r'\*(.+?)\*', r'\1', clean)
        clean = re.sub(r'^#+\s+', '', clean, flags=re.MULTILINE)
        clean = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean)
        clean = clean.strip()[:max_chars]
        self.tts.speak(clean, block=False)

    def is_voice_available(self) -> bool:
        return self.tts.is_available() or self.stt.is_available()

    def status(self) -> str:
        return f'TTS={self.tts.backend}  STT={self.stt.backend}'


# ── Module-level singleton ───────────────────────────────────────────────────

_session: Optional[VoiceSession] = None

def get_voice_session() -> VoiceSession:
    global _session
    if _session is None:
        _session = VoiceSession(
            tts_backend=_TTS_BACKEND,
            stt_backend=_STT_BACKEND,
        )
    return _session


def tool_voice_listen(timeout: int = 10) -> str:
    """Listen for voice input and return transcribed text."""
    v = get_voice_session()
    if not v.stt.is_available():
        return 'ERROR: No STT backend available. Install: pip install SpeechRecognition PyAudio'
    text = v.listen_and_transcribe(timeout=timeout)
    if text:
        return f'Heard: {text}'
    return 'No speech detected or could not transcribe.'


def tool_voice_speak(text: str) -> str:
    """Speak text aloud using TTS."""
    v = get_voice_session()
    if not v.tts.is_available():
        return 'ERROR: No TTS backend available. Install: pip install pyttsx3'
    v.speak_response(text)
    return f'Speaking: {text[:80]}'


def tool_voice_status() -> str:
    """Return current voice backend status."""
    v = get_voice_session()
    return f'Voice: {v.status()}'
