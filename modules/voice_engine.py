"""
Voice engine for Devin-4.0.
STT (speech-to-text) + TTS (text-to-speech) with graceful fallback.
"""

import os
import sys
import tempfile
import threading
import queue
import time
from typing import Optional, Callable

_IS_LINUX = sys.platform.startswith("linux")
_IS_MAC = sys.platform == "darwin"
_IS_WIN = sys.platform.startswith("win")

_HAS_PYTTSX3 = False
try:
    import pyttsx3
    _HAS_PYTTSX3 = True
except ImportError:
    pass

_HAS_GTTS = False
try:
    from gtts import gTTS
    _HAS_GTTS = True
except ImportError:
    pass

_HAS_SPEECHRECOGNITION = False
try:
    import speech_recognition as sr
    _HAS_SPEECHRECOGNITION = True
except ImportError:
    pass

_HAS_WHISPER = False
try:
    import whisper as openai_whisper
    _HAS_WHISPER = True
except ImportError:
    pass

_HAS_PYAUDIO = False
try:
    import pyaudio
    _HAS_PYAUDIO = True
except ImportError:
    pass


class VoiceEngine:
    """Voice I/O engine with multiple STT/TTS backend fallbacks."""

    def __init__(
        self,
        tts_backend: str = "auto",
        stt_backend: str = "auto",
        tts_rate: int = 175,
        tts_volume: float = 0.9,
        language: str = "en",
        on_speech: Optional[Callable[[str], None]] = None,
    ):
        self.tts_backend = tts_backend
        self.stt_backend = stt_backend
        self.tts_rate = tts_rate
        self.tts_volume = tts_volume
        self.language = language
        self.on_speech = on_speech

        self._pyttsx3_engine = None
        self._whisper_model = None
        self._sr_recognizer = None
        self._listen_thread: Optional[threading.Thread] = None
        self._listen_active = False
        self._speech_queue: queue.Queue = queue.Queue()

        self._init_tts()
        self._init_stt()

    # --- TTS init ---

    def _init_tts(self) -> None:
        if self.tts_backend in ("pyttsx3", "auto") and _HAS_PYTTSX3:
            try:
                self._pyttsx3_engine = pyttsx3.init()
                self._pyttsx3_engine.setProperty("rate", self.tts_rate)
                self._pyttsx3_engine.setProperty("volume", self.tts_volume)
                self.tts_backend = "pyttsx3"
                return
            except Exception:
                pass
        if self.tts_backend in ("gtts", "auto") and _HAS_GTTS:
            self.tts_backend = "gtts"
            return
        if self.tts_backend == "auto":
            self.tts_backend = "system"

    def _init_stt(self) -> None:
        if self.stt_backend in ("whisper", "auto") and _HAS_WHISPER:
            try:
                self._whisper_model = openai_whisper.load_model("base")
                self.stt_backend = "whisper"
                return
            except Exception:
                pass
        if self.stt_backend in ("google", "auto") and _HAS_SPEECHRECOGNITION:
            try:
                self._sr_recognizer = sr.Recognizer()
                self.stt_backend = "google"
                return
            except Exception:
                pass
        self.stt_backend = "none"

    # --- TTS speak ---

    def speak(self, text: str) -> str:
        if not text:
            return "OK"
        text = text.strip()
        if self.tts_backend == "pyttsx3" and self._pyttsx3_engine:
            return self._speak_pyttsx3(text)
        if self.tts_backend == "gtts":
            return self._speak_gtts(text)
        if self.tts_backend == "system":
            return self._speak_system(text)
        return "ERROR: no TTS backend available (install pyttsx3 or gtts)"

    def _speak_pyttsx3(self, text: str) -> str:
        try:
            self._pyttsx3_engine.say(text)
            self._pyttsx3_engine.runAndWait()
            return "OK"
        except Exception as e:
            return f"ERROR: pyttsx3 speak failed: {e}"

    def _speak_gtts(self, text: str) -> str:
        try:
            tts = gTTS(text=text, lang=self.language, slow=False)
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                tmp = f.name
            tts.save(tmp)
            result = self._play_audio(tmp)
            try:
                os.unlink(tmp)
            except OSError:
                pass
            return result
        except Exception as e:
            return f"ERROR: gtts speak failed: {e}"

    def _speak_system(self, text: str) -> str:
        import subprocess
        if _IS_MAC:
            try:
                subprocess.run(["say", text], timeout=60, check=False)
                return "OK"
            except Exception as e:
                return f"ERROR: say command failed: {e}"
        if _IS_LINUX:
            for cmd in [
                ["espeak", text],
                ["espeak-ng", text],
                ["spd-say", text],
            ]:
                try:
                    proc = subprocess.run(cmd, timeout=30, check=False)
                    if proc.returncode == 0:
                        return "OK"
                except FileNotFoundError:
                    pass
                except Exception:
                    pass
            try:
                proc = subprocess.run(
                    ["festival", "--tts"],
                    input=text.encode(),
                    timeout=30,
                    check=False,
                )
                if proc.returncode == 0:
                    return "OK"
            except (FileNotFoundError, Exception):
                pass
            return "ERROR: no TTS binary found (install espeak or festival)"
        if _IS_WIN:
            text_safe = text.replace('"', '\\"')
            try:
                ps_script = (
                    "Add-Type -AssemblyName System.Speech; "
                    "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                    f'$s.Speak("{text_safe}")'
                )
                subprocess.run(
                    ["powershell", "-Command", ps_script], timeout=60, check=False
                )
                return "OK"
            except Exception as e:
                return f"ERROR: PowerShell TTS failed: {e}"
        return "ERROR: no TTS available on this platform"

    def _play_audio(self, path: str) -> str:
        import subprocess
        if _IS_MAC:
            try:
                subprocess.run(["afplay", path], timeout=120, check=False)
                return "OK"
            except Exception:
                pass
        if _IS_LINUX:
            for player in ["mpg123", "mpg321", "ffplay", "aplay", "paplay"]:
                try:
                    subprocess.run([player, path], timeout=120, check=False)
                    return "OK"
                except FileNotFoundError:
                    pass
        if _IS_WIN:
            try:
                import winsound
                winsound.PlaySound(path, winsound.SND_FILENAME)
                return "OK"
            except Exception:
                pass
        return "ERROR: no audio player found"

    # --- STT listen ---

    def listen_once(self, timeout: float = 10.0, phrase_timeout: float = 5.0) -> str:
        if self.stt_backend == "whisper":
            return self._listen_whisper(timeout)
        if self.stt_backend == "google":
            return self._listen_google(timeout, phrase_timeout)
        return "ERROR: no STT backend available (install speech_recognition or openai-whisper)"

    def _listen_google(self, timeout: float, phrase_timeout: float) -> str:
        if not _HAS_SPEECHRECOGNITION or not _HAS_PYAUDIO:
            return "ERROR: install SpeechRecognition and pyaudio"
        try:
            with sr.Microphone() as source:
                self._sr_recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self._sr_recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_timeout
                )
            text = self._sr_recognizer.recognize_google(audio, language=self.language)
            return text
        except sr.WaitTimeoutError:
            return "ERROR: no speech detected within timeout"
        except sr.UnknownValueError:
            return "ERROR: could not understand audio"
        except sr.RequestError as e:
            return f"ERROR: Google STT request failed: {e}"
        except Exception as e:
            return f"ERROR: listen failed: {e}"

    def _listen_whisper(self, timeout: float) -> str:
        if not _HAS_WHISPER or not _HAS_PYAUDIO:
            return "ERROR: install openai-whisper and pyaudio"
        try:
            RATE = 16000
            CHUNK = 1024
            pa = pyaudio.PyAudio()
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
            )
            frames = []
            for _ in range(int(RATE / CHUNK * timeout)):
                frames.append(stream.read(CHUNK, exception_on_overflow=False))
            stream.stop_stream()
            stream.close()
            pa.terminate()

            import wave
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                tmp = f.name
            wf = wave.open(tmp, "wb")
            wf.setnchannels(1)
            wf.setsampwidth(pa.get_sample_size(pyaudio.paInt16))
            wf.setframerate(RATE)
            wf.writeframes(b"".join(frames))
            wf.close()

            lang = self.language if self.language != "en" else None
            result = self._whisper_model.transcribe(tmp, language=lang)
            try:
                os.unlink(tmp)
            except OSError:
                pass
            return result.get("text", "").strip()
        except Exception as e:
            return f"ERROR: whisper transcription failed: {e}"

    # --- Continuous listening ---

    def start_continuous_listening(self) -> None:
        if self._listen_active:
            return
        self._listen_active = True
        self._listen_thread = threading.Thread(
            target=self._continuous_loop, daemon=True
        )
        self._listen_thread.start()

    def stop_continuous_listening(self) -> None:
        self._listen_active = False
        if self._listen_thread:
            self._listen_thread.join(timeout=5)

    def _continuous_loop(self) -> None:
        while self._listen_active:
            result = self.listen_once(timeout=5.0)
            if not result.startswith("ERROR:") and result.strip():
                if self.on_speech:
                    try:
                        self.on_speech(result)
                    except Exception:
                        pass
                self._speech_queue.put(result)

    def get_pending_speech(self, block: bool = False, timeout: float = 0.1) -> Optional[str]:
        try:
            return self._speech_queue.get(block=block, timeout=timeout)
        except queue.Empty:
            return None

    # --- Transcribe file ---

    def transcribe_file(self, audio_path: str) -> str:
        if not os.path.exists(audio_path):
            return f"ERROR: file not found: {audio_path}"
        if self._whisper_model:
            try:
                result = self._whisper_model.transcribe(audio_path)
                return result.get("text", "").strip()
            except Exception as e:
                return f"ERROR: whisper transcription failed: {e}"
        if self._sr_recognizer and _HAS_SPEECHRECOGNITION:
            try:
                with sr.AudioFile(audio_path) as source:
                    audio = self._sr_recognizer.record(source)
                return self._sr_recognizer.recognize_google(audio)
            except Exception as e:
                return f"ERROR: Google STT transcription failed: {e}"
        return "ERROR: no STT backend available"

    def status(self) -> str:
        lines = ["Voice Engine Status:"]
        lines.append(f"  TTS backend: {self.tts_backend}")
        lines.append(f"  STT backend: {self.stt_backend}")
        lines.append(f"  Language: {self.language}")
        lines.append(f"  Continuous listening: {self._listen_active}")
        if self.tts_backend == "none":
            lines.append("  TTS: install pyttsx3 or gtts")
        if self.stt_backend == "none":
            lines.append("  STT: install speech_recognition or openai-whisper")
        return "\n".join(lines)


_voice_instance: Optional[VoiceEngine] = None


def get_voice_engine(**kwargs) -> VoiceEngine:
    global _voice_instance
    if _voice_instance is None:
        _voice_instance = VoiceEngine(**kwargs)
    return _voice_instance


def speak(text: str) -> str:
    return get_voice_engine().speak(text)


def listen(timeout: float = 10.0) -> str:
    return get_voice_engine().listen_once(timeout=timeout)


def transcribe(audio_path: str) -> str:
    return get_voice_engine().transcribe_file(audio_path)
