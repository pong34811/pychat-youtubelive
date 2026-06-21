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
    def __init__(self, voice: str = "th-TH-PremwadeeNeural") -> None:
        self.voice = voice
        self.queue: queue.Queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        try:
            pygame.mixer.init()
        except Exception:
            pass

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def speak(self, name: str, message: str) -> None:
        text = message.strip()
        if not text:
            return
        text = EMOJI_PATTERN.sub("", text).strip()
        if len(text) < MIN_TEXT_LENGTH:
            return
        if len(text) > MAX_TEXT_LENGTH:
            text = text[:MAX_TEXT_LENGTH]
        self.queue.put((name, text))

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
                tts = edge_tts.Communicate(sentence, voice=self.voice)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                    tmp_path = f.name
                asyncio.run(tts.save(tmp_path))
                pygame.mixer.music.load(tmp_path)
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
                print(f"TTS Error: {e}")
