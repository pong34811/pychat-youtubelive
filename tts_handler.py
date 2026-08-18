import asyncio
import os
import queue
import re
import tempfile
import threading
import logging

import edge_tts
import pygame

# Project imports
from config.constants import EMOJI_REGEX, MIN_TTS_MESSAGE_LEN, MAX_TTS_MESSAGE_LEN, DEFAULT_TTS_VOICE

logger = logging.getLogger(__name__)


EMOJI_PATTERN = re.compile(EMOJI_REGEX)
MAX_TEXT_LENGTH = MAX_TTS_MESSAGE_LEN
MIN_TEXT_LENGTH = MIN_TTS_MESSAGE_LEN


class TTSHandler:
    def __init__(self, message_queue: queue.Queue | None = None, voice: str = DEFAULT_TTS_VOICE) -> None:
        self.voice = voice
        self.volume: float = 0.5
        self.rate: str = "-15%"   # ความเร็วในการอ่าน (ค่าลบ = ช้าลง, ค่าบวก = เร็วขึ้น)
        self.queue: queue.Queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._msg_q = message_queue
        try:
            pygame.mixer.init()
        except Exception as e:
            self._debug(f"pygame init failed: {e}")

    def set_volume(self, volume: float) -> None:
        self.volume = max(0.0, min(1.0, volume))

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def speak(self, name: str, message: str) -> None:
        # Remove leading @ from usernames
        name = name.lstrip("@")
        # Initial whitespace stripping
        text = message.strip()
        if not text:
            logger.debug("speak skipped: empty after initial strip")
            return
        # Remove colon‑style emoji placeholders
        text = EMOJI_PATTERN.sub("", text)
        # Remove any Unicode emoji characters (covers Supplementary Plane)
        text = re.sub(r"[\U00010000-\U0010FFFF]+", "", text)
        # Final strip to clean up spaces left by removals
        text = text.strip()
        if not text:
            logger.debug("speak skipped: message became empty after emoji removal")
            return
        if len(text) < MIN_TEXT_LENGTH:
            logger.debug(f"speak skipped: too short ({len(text)} chars)")
            return
        if len(text) > MAX_TEXT_LENGTH:
            text = text[:MAX_TEXT_LENGTH]
        logger.debug(f"speak queued: {name} said {text[:50]}")
        self.queue.put((name, text))

    def _debug(self, msg: str) -> None:
        if self._msg_q:
            self._msg_q.put(("TTS", "[ระบบ]", f"⚙️ {msg}"))
        else:
            logger.debug(msg)

    def stop(self) -> None:
        self._stop_event.set()
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except queue.Empty:
                break

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                name, text = self.queue.get(timeout=1)
            except queue.Empty:
                continue
            sentence = f"{name} กล่าวว่า {text}"
            try:
                tts = edge_tts.Communicate(sentence, voice=self.voice, rate=self.rate)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                    tmp_path = f.name
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(tts.save(tmp_path))
                finally:
                    loop.close()
                pygame.mixer.music.load(tmp_path)
                pygame.mixer.music.set_volume(self.volume)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy() and not self._stop_event.is_set():
                    threading.Event().wait(0.1)
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
            except Exception as e:
                self._debug(f"TTS error: {e}")
