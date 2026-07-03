import asyncio
import os
import queue
import re
import tempfile
import threading

import edge_tts
import pygame


EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002600-\U000026FF"
    "\U0000FE00-\U0000FE0F"
    "]+"
)
MAX_TEXT_LENGTH = 200
MIN_TEXT_LENGTH = 2


class TTSHandler:
    def __init__(self, message_queue: queue.Queue | None = None, voice: str = "th-TH-PremwadeeNeural") -> None:
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
        name = name.lstrip("@")  # นำ @ ออกจากชื่อผู้ใช้
        text = message.strip()
        if not text:
            self._debug(f"speak skipped: empty after strip")
            return
        text = EMOJI_PATTERN.sub("", text).strip()
        if len(text) < MIN_TEXT_LENGTH:
            self._debug(f"speak skipped: too short ({len(text)} chars)")
            return
        if len(text) > MAX_TEXT_LENGTH:
            text = text[:MAX_TEXT_LENGTH]
        self._debug(f"speak queued: {name} กล่าวว่า {text[:50]}")
        self.queue.put((name, text))

    def _debug(self, msg: str) -> None:
        if self._msg_q:
            self._msg_q.put(("TTS", "[ระบบ]", f"⚙️ {msg}"))

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
