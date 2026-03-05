"""
voice_engine.py — Unified TTS + STT for JARVIS
Supports online (Google STT) and offline (pocketsphinx fallback) modes
"""

import threading
import queue
import pyttsx3
import speech_recognition as sr
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import VOICE_INDEX, SPEECH_RATE, USER_NAME, OFFLINE_FALLBACK

# ── TTS ENGINE (thread-safe singleton) ───────────────────────

class TTSEngine:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_engine()
            return cls._instance

    def _init_engine(self):
        self._engine = pyttsx3.init("sapi5")
        voices = self._engine.getProperty("voices")
        # Use configured voice, fallback to first available
        idx = min(VOICE_INDEX, len(voices) - 1)
        self._engine.setProperty("voice", voices[idx].id)
        self._engine.setProperty("rate", SPEECH_RATE)
        self._engine.setProperty("volume", 0.9)
        self._speak_lock = threading.Lock()
        self._queue = queue.Queue()
        self._speaking = False

    def speak(self, text: str, priority: bool = False):
        """Speak text. If priority=True, interrupts current speech."""
        if not text or text.strip() in ("None", "", "null"):
            return
        print(f"\n🤖 {text}\n")
        with self._speak_lock:
            self._speaking = True
            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except Exception as e:
                print(f"[TTS Error]: {e}")
                # Re-init engine if it crashes
                self._init_engine()
            finally:
                self._speaking = False

    def is_speaking(self):
        return self._speaking

    def set_rate(self, rate: int):
        self._engine.setProperty("rate", rate)

    def set_voice(self, index: int):
        voices = self._engine.getProperty("voices")
        idx = min(index, len(voices) - 1)
        self._engine.setProperty("voice", voices[idx].id)


# Global TTS instance
_tts = TTSEngine()

def speak(text: str, priority: bool = False):
    """Global speak function."""
    _tts.speak(text, priority)

def speak_async(text: str):
    """Fire-and-forget speak in background thread."""
    t = threading.Thread(target=speak, args=(text,), daemon=True)
    t.start()


# ── STT ENGINE ────────────────────────────────────────────────

class STTEngine:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 0.8
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True

    def listen(self, timeout: int = 5, phrase_limit: int = 10) -> str:
        """
        Listen from microphone and return text.
        Returns 'None' on failure.
        """
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                print("👂 Listening...")
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_limit
                )
        except sr.WaitTimeoutError:
            return "None"
        except Exception as e:
            print(f"[Mic Error]: {e}")
            return "None"

        return self._recognize(audio)

    def _recognize(self, audio) -> str:
        """Try Google STT, fall back to offline if needed."""
        # Try online first
        try:
            text = self.recognizer.recognize_google(audio, language="en-in")
            print(f"🗣️  You: {text}")
            return text
        except sr.UnknownValueError:
            return "None"
        except sr.RequestError:
            # No internet — try offline fallback
            if OFFLINE_FALLBACK:
                return self._offline_recognize(audio)
            return "None"

    def _offline_recognize(self, audio) -> str:
        """Offline STT using Vosk or sphinx."""
        try:
            text = self.recognizer.recognize_sphinx(audio)
            print(f"🗣️  You (offline): {text}")
            return text
        except Exception:
            return "None"

    def listen_for_wake_word(self, wake_word: str = "jarvis") -> bool:
        """
        Lightweight continuous listen for wake word.
        Returns True when wake word detected.
        """
        result = self.listen(timeout=3, phrase_limit=3)
        return wake_word.lower() in result.lower()


# Global STT instance
_stt = STTEngine()

def take_command(timeout: int = 5, phrase_limit: int = 10) -> str:
    return _stt.listen(timeout=timeout, phrase_limit=phrase_limit)

def listen_for_wake_word(word: str = "jarvis") -> bool:
    return _stt.listen_for_wake_word(word)
