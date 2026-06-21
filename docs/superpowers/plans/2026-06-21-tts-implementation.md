# TTS Feature Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add edge-tts based TTS that reads YouTube Live chat messages aloud in natural Thai voice.

**Architecture:** Background thread with `queue.Queue` consumes messages from the main chat loop and speaks them sequentially using edge-tts, so TTS never blocks the chat reader.

**Tech Stack:** Python 3.9+, edge-tts, threading, queue, pygame (for audio playback)

## Global Constraints

- Python 3.9+
- Type hints on all functions
- User-facing messages in Thai
- No blocking the main chat loop
- Edge-tts must not crash the main loop on failure
- All network calls wrapped in try/except

---

### Task 1: `tts_handler.py` — TTS Engine

**Files:**
- Create: `tts_handler.py`
- Create: `tests/test_tts_handler.py`
- Modify: `requirements.txt` (add edge-tts, pygame)

**Interfaces:**
- Consumes: nothing (standalone utility)
- Produces: `class TTSHandler` with `__init__(voice: str)`, `start()`, `speak(name: str, message: str)`, `stop()`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_tts_handler.py
import pytest
from tts_handler import TTSHandler


def test_speak_queues_message():
    handler = TTSHandler(voice="th-TH-PremmawadeeNeural")
    handler.start()
    handler.speak("John", "สวัสดี")
    assert handler.queue.qsize() == 1
    name, text = handler.queue.get_nowait()
    assert name == "John"
    assert text == "สวัสดี"
    handler.stop()


def test_empty_message_skipped():
    handler = TTSHandler()
    handler.start()
    handler.speak("John", "")
    assert handler.queue.qsize() == 0
    handler.stop()


def test_short_message_skipped():
    handler = TTSHandler()
    handler.start()
    handler.speak("John", "อ")
    assert handler.queue.qsize() == 0
    handler.stop()


def test_emoji_only_message_skipped():
    handler = TTSHandler()
    handler.start()
    handler.speak("John", "😂😂")
    assert handler.queue.qsize() == 0
    handler.stop()


def test_long_message_truncated():
    handler = TTSHandler()
    handler.start()
    long_msg = "a" * 300
    handler.speak("John", long_msg)
    name, text = handler.queue.get_nowait()
    assert len(text) <= 200
    handler.stop()


def test_stop_clears_queue():
    handler = TTSHandler()
    handler.start()
    handler.speak("John", "hello")
    handler.stop()
    assert handler.queue.qsize() == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```powershell
python -m pytest tests/test_tts_handler.py -v
```
Expected: FAIL with ModuleNotFoundError (tts_handler doesn't exist yet)

- [ ] **Step 3: Write minimal implementation**

```python
# tts_handler.py
import queue
import re
import threading
import tempfile
import os

import edge_tts


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
    def __init__(self, voice: str = "th-TH-PremmawadeeNeural") -> None:
        self.voice = voice
        self.queue: queue.Queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

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
        import pygame

        pygame.mixer.init()
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
                import asyncio
                asyncio.run(tts.save(tmp_path))
                pygame.mixer.music.load(tmp_path)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy() and not self._stop_event.is_set():
                    threading.Event().wait(0.1)
                os.unlink(tmp_path)
            except Exception as e:
                print(f"TTS Error: {e}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```powershell
python -m pytest tests/test_tts_handler.py -v
```
Expected: PASS (tests check queue logic without calling edge-tts)

- [ ] **Step 5: Install dependencies**

Run:
```powershell
pip install edge-tts pygame
```

- [ ] **Step 6: Update requirements.txt**

Run:
```powershell
pip freeze | Select-String "edge-tts|pygame" >> requirements.txt
```

- [ ] **Step 7: Commit**

```powershell
git add tts_handler.py tests/test_tts_handler.py requirements.txt
git commit -m "feat: add TTSHandler with edge-tts and queue-based threading"
```

---

### Task 2: Integrate TTS into `main.py`

**Files:**
- Modify: `main.py`

**Interfaces:**
- Consumes: `TTSHandler` from `tts_handler.py`
- Produces: chat messages printed + spoken via TTS

- [ ] **Step 1: Update main.py**

Edit `main.py`:
- Add import for `TTSHandler`
- Create and start TTS handler before chat loop
- Call `tts.speak()` after `print()` in the loop
- Stop TTS on exit

```python
# main.py
import time

import httpx
import pytchat

from fix_message import sanitize_message
from tts_handler import TTSHandler


def get_video_id(text: str) -> str:
    if "v=" in text:
        return text.split("v=")[-1].split("&")[0]
    if "youtu.be/" in text:
        return text.split("youtu.be/")[-1]
    return text


def get_youtubechat(video_id: str) -> None:
    chat = pytchat.create(video_id=video_id)
    tts = TTSHandler()
    tts.start()

    while chat.is_alive():
        try:
            items = chat.get().sync_items()
        except httpx.ReadTimeout:
            print("เชื่อมต่อช้า กำลังลองใหม่ใน 3 วินาที...")
            time.sleep(3)
            continue

        for c in items:
            clean_message = sanitize_message(c.message)
            if not clean_message:
                continue
            print(f"{c.author.name}: {clean_message}")
            tts.speak(c.author.name, clean_message)

    tts.stop()


def main() -> None:
    print("วางลิงก์ YouTube Live หรือ video id")
    url = input("> ")

    video_id = get_video_id(url)
    print("กำลังอ่านแชต...\n")

    try:
        get_youtubechat(video_id)
    except KeyboardInterrupt:
        print("หยุดแล้ว")
    except Exception as error:
        print(f"เกิดข้อผิดพลาด: {error}")
        print("ตรวจสอบว่าลิงก์เป็นไลฟ์จริง, แชตเปิดอยู่, และอินเทอร์เน็ตเชื่อมต่อปกติ")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the program to verify**

Run:
```powershell
python main.py
```
Expected: Program runs, accepts URL, prints chat, and speaks messages aloud

- [ ] **Step 3: Commit**

```powershell
git add main.py
git commit -m "feat: integrate TTSHandler into main chat loop"
```

---

### Task 3: Create `tests/__init__.py` and verify all tests pass

**Files:**
- Create: `tests/__init__.py`

- [ ] **Step 1: Create `tests/__init__.py`**

```python
# tests/__init__.py
```

- [ ] **Step 2: Run all tests**

```powershell
python -m pytest tests/ -v
```
Expected: PASS

- [ ] **Step 3: Commit**

```powershell
git add tests/__init__.py
git commit -m "chore: add tests package init and verify all tests pass"
```
