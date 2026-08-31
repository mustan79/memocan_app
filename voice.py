from __future__ import annotations
import logging
import queue
import threading
from config import config_dir

LOG_PATH = config_dir() / "memocan.log"
logging.basicConfig(filename=LOG_PATH, level=logging.INFO, encoding="utf-8", format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("memocan.voice")

class Voice:
    def __init__(self, enabled=True, language="tr", microphone_index=-1):
        self.enabled, self.language = enabled, language
        self.microphone_index = microphone_index if microphone_index >= 0 else self.best_microphone_index()
        self._queue, self._ready = queue.Queue(), threading.Event()
        self.tts_available = False
        threading.Thread(target=self._speech_loop, daemon=True, name="memocan-tts").start()
        self._ready.wait(5)

    def _speech_loop(self):
        engine = None
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("volume", 1.0); engine.setProperty("rate", 175)
            self.tts_available = True
            log.info("TTS engine initialized")
        except Exception:
            log.exception("TTS initialization failed")
        self._ready.set()
        while True:
            item = self._queue.get()
            if item is None: return
            text, done, result = item
            try:
                if engine:
                    engine.stop(); engine.say(text); engine.runAndWait(); result.append(True)
                else: result.append(False)
            except Exception:
                log.exception("TTS playback failed"); result.append(False)
            finally:
                done.set()

    @property
    def recognition_language(self):
        return "tr-TR" if self.language == "tr" else "en-US"

    def speak(self, text: str, force=False, wait=True):
        if not ((self.enabled or force) and text): return False
        done, result = threading.Event(), []
        self._queue.put((text, done, result))
        if not wait: return True
        done.wait(20)
        return bool(result and result[0])

    def beep(self):
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception:
            print("\a", end="", flush=True)

    def alert(self, text: str):
        if not self.speak(text): self.beep()

    def listen_once(self, timeout=5, phrase_time_limit=15, calibrate=0.35):
        try:
            import speech_recognition as sr
            rec = sr.Recognizer()
            with sr.Microphone(device_index=self.microphone_index) as source:
                if calibrate: rec.adjust_for_ambient_noise(source, duration=calibrate)
                audio = rec.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            text = rec.recognize_google(audio, language=self.recognition_language)
            log.info("Speech recognized (%s)", self.recognition_language)
            return text, None
        except Exception as exc:
            log.info("Speech recognition ended: %s", exc.__class__.__name__)
            return None, exc.__class__.__name__

    @staticmethod
    def microphone_names():
        try:
            import speech_recognition as sr
            return sr.Microphone.list_microphone_names()
        except Exception:
            log.exception("Microphone enumeration failed")
            return []

    @classmethod
    def best_microphone_index(cls):
        names = cls.microphone_names()
        preferred = ("mikrofon dizisi", "microphone array")
        for index, name in enumerate(names):
            if any(label in name.casefold() for label in preferred): return index
        return -1

    def close(self):
        self._queue.put(None)
