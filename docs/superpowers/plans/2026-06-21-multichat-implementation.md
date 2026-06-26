# Multi-Chat Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add TikTok and Twitch chat support alongside existing YouTube chat in the GUI, with per-platform input, status indicator, and platform prefix in messages.

**Architecture:** Each platform has its own worker module + thread that puts `(platform, name, text)` tuples into a shared queue. GUI polls the queue and displays with `[YT]`, `[TT]`, `[TW]` prefixes.

**Tech Stack:** Python 3.9+, pytchat, TikTokLive, IRC (socket), customtkinter, threading, queue

## Global Constraints
- Type hints all functions
- User-facing text in Thai
- Non-blocking GUI (workers in threads)
- Error in one platform must not crash others
- Track `.gitignore` for build artifacts

---

### Task 1: Create `chat_workers/` package

**Files:**
- Create: `chat_workers/__init__.py`
- Create: `chat_workers/base_worker.py`

- [ ] **Step 1: Create package files**

```python
# chat_workers/__init__.py
from .youtube_worker import YouTubeWorker
from .tiktok_worker import TikTokWorker
from .twitch_worker import TwitchWorker

__all__ = ["YouTubeWorker", "TikTokWorker", "TwitchWorker"]
```

```python
# chat_workers/base_worker.py
from abc import ABC, abstractmethod
import queue
import threading


class BaseWorker(ABC):
    def __init__(self, message_queue: queue.Queue) -> None:
        self.message_queue = message_queue
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    @abstractmethod
    def _run(self) -> None:
        ...

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    @property
    def is_alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive()
```

- [ ] **Step 2: Commit**

```powershell
git add chat_workers/
git commit -m "feat: add chat_workers package with base worker"
```

---

### Task 2: YouTube Worker — extract from gui.py

**Files:**
- Create: `chat_workers/youtube_worker.py`
- Modify: `gui.py` (replace inline pytchat with worker)

- [ ] **Step 1: Write youtube_worker.py**

```python
# chat_workers/youtube_worker.py
import time
import queue
import httpx
import pytchat

from fix_message import sanitize_message
from .base_worker import BaseWorker


PLATFORM = "YT"


class YouTubeWorker(BaseWorker):
    def __init__(self, video_id: str, message_queue: queue.Queue) -> None:
        super().__init__(message_queue)
        self.video_id = video_id
        self.chat = None

    def _run(self) -> None:
        try:
            self.chat = pytchat.create(video_id=self.video_id)
        except Exception as e:
            self.message_queue.put((PLATFORM, "[ระบบ]", f"❌ YouTube: {e}"))
            return

        while not self._stop_event.is_set() and self.chat.is_alive():
            try:
                items = self.chat.get().sync_items()
            except httpx.ReadTimeout:
                time.sleep(3)
                continue

            for c in items:
                if self._stop_event.is_set():
                    return
                clean = sanitize_message(c.message)
                if not clean:
                    continue
                self.message_queue.put((PLATFORM, c.author.name, clean))

        if not self._stop_event.is_set():
            self.message_queue.put((PLATFORM, "[ระบบ]", "📴 YouTube chat ended"))
```

- [ ] **Step 2: Update gui.py** — replace inline _chat_loop with YouTubeWorker

Edit `gui.py`:
- Remove `_chat_loop` method
- In `_start_chat`: create `YouTubeWorker(video_id, self._message_queue)` and call `.start()`
- Add `self._workers = []` in `__init__`
- In `_poll_messages`: accept `(platform, name, text)` format, display as `[{platform}] {name}: {text}`
- In `_on_close`: stop all workers

- [ ] **Step 3: Commit**

```powershell
git add chat_workers/youtube_worker.py gui.py
git commit -m "feat: extract YouTube chat to worker, update GUI for multi-platform format"
```

---

### Task 3: TikTok Worker

**Files:**
- Create: `chat_workers/tiktok_worker.py`

- [ ] **Step 1: Write tiktok_worker.py**

```python
# chat_workers/tiktok_worker.py
import asyncio
import queue
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent

from fix_message import sanitize_message
from .base_worker import BaseWorker


PLATFORM = "TT"


class TikTokWorker(BaseWorker):
    def __init__(self, username: str, message_queue: queue.Queue) -> None:
        super().__init__(message_queue)
        self.username = username.strip("@")

    def _run(self) -> None:
        async def _connect():
            client = TikTokLiveClient(unique_id=self.username)

            @client.on("connect")
            async def on_connect(_):
                self.message_queue.put((PLATFORM, "[ระบบ]", "✅ TikTok connected"))

            @client.on("disconnect")
            async def on_disconnect(_):
                self.message_queue.put((PLATFORM, "[ระบบ]", "🔌 TikTok disconnected"))

            @client.on(CommentEvent)
            async def on_comment(event: CommentEvent):
                if self._stop_event.is_set():
                    await client.disconnect()
                    return
                text = sanitize_message(event.comment)
                if text:
                    self.message_queue.put((PLATFORM, event.user.unique_id, text))

            try:
                await client.start()
            except Exception as e:
                self.message_queue.put((PLATFORM, "[ระบบ]", f"❌ TikTok: {e}"))

        asyncio.run(_connect())
```

- [ ] **Step 2: Add TikTok input to GUI**

In `gui.py`:
- Add TikTok username entry + Start button
- On start: create `TikTokWorker(username, self._message_queue)` and `.start()`

- [ ] **Step 3: Commit**

```powershell
git add chat_workers/tiktok_worker.py gui.py
git commit -m "feat: add TikTok chat worker"
```

---

### Task 4: Twitch Worker

**Files:**
- Create: `chat_workers/twitch_worker.py`
- Create: `chat_workers/twitch_auth.py`

- [ ] **Step 1: Write twitch_auth.py** — OAuth token generator

```python
# chat_workers/twitch_auth.py
import socket
import threading
import urllib.parse
import webbrowser

CLIENT_ID = "dezbvkl619rp5g83gyezee3itn3alg"
SCOPE = "chat:read"
REDIRECT_URI = "http://localhost"


def get_oauth_token() -> str | None:
    auth_url = (
        f"https://id.twitch.tv/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=token"
        f"&scope={SCOPE}"
        f"&force_verify=true"
    )

    token = None
    event = threading.Event()

    def _server():
        nonlocal token
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("127.0.0.1", 80))
        server.listen(1)
        server.settimeout(120)
        conn, _ = server.accept()
        data = conn.recv(4096).decode()
        if "access_token=" in data:
            fragment = data.split("access_token=")[1].split("&")[0]
            token = fragment
        conn.send(b"HTTP/1.1 200 OK\r\n\r\nDone, close this window.")
        conn.close()
        server.close()
        event.set()

    t = threading.Thread(target=_server, daemon=True)
    t.start()
    webbrowser.open(auth_url)
    event.wait(timeout=120)
    return token
```

- [ ] **Step 2: Write twitch_worker.py** — IRC chat reader

```python
# chat_workers/twitch_worker.py
import socket
import queue
import re

from fix_message import sanitize_message
from .base_worker import BaseWorker
from .twitch_auth import get_oauth_token, CLIENT_ID


PLATFORM = "TW"
IRC_HOST = "irc.chat.twitch.tv"
IRC_PORT = 6667
MESSAGE_PATTERN = re.compile(r":(\w+)!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :(.+)")


class TwitchWorker(BaseWorker):
    def __init__(self, channel: str, message_queue: queue.Queue) -> None:
        super().__init__(message_queue)
        self.channel = channel.strip("#").lower()
        self._token = None

    def _run(self) -> None:
        self._token = get_oauth_token()
        if not self._token:
            self.message_queue.put((PLATFORM, "[ระบบ]", "❌ Twitch: ไม่ได้รับ token"))
            return

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((IRC_HOST, IRC_PORT))
            sock.send(f"PASS oauth:{self._token}\r\n".encode())
            sock.send(f"NICK {self.channel}\r\n".encode())
            sock.send(f"JOIN #{self.channel}\r\n".encode())
            sock.settimeout(1)
        except Exception as e:
            self.message_queue.put((PLATFORM, "[ระบบ]", f"❌ Twitch: {e}"))
            return

        self.message_queue.put((PLATFORM, "[ระบบ]", f"✅ Twitch:  joined #{self.channel}"))

        while not self._stop_event.is_set():
            try:
                data = sock.recv(2048).decode(errors="ignore")
            except socket.timeout:
                continue
            except Exception as e:
                self.message_queue.put((PLATFORM, "[ระบบ]", f"❌ Twitch: {e}"))
                break

            for line in data.split("\r\n"):
                if line.startswith("PING"):
                    sock.send(line.replace("PING", "PONG").encode() + b"\r\n")
                    continue
                match = MESSAGE_PATTERN.match(line)
                if match:
                    name, text = match.group(1), match.group(2)
                    clean = sanitize_message(text)
                    if clean:
                        self.message_queue.put((PLATFORM, name, clean))

        sock.close()
```

- [ ] **Step 3: Add Twitch input to GUI**

In `gui.py`:
- Add Twitch channel entry + Start button
- On start: create `TwitchWorker(channel, self._message_queue)` and `.start()`

- [ ] **Step 4: Commit**

```powershell
git add chat_workers/twitch_worker.py chat_workers/twitch_auth.py gui.py
git commit -m "feat: add Twitch chat worker with OAuth PKCE flow"
```

---

### Task 5: Update GUI layout for multi-platform

**Files:**
- Modify: `gui.py` — full redesign

- [ ] **Step 1: Redesign gui.py**

```python
# Partial structure:

class ChatGUI(ctk.CTk):
    def __init__(self):
        ...
        self._message_queue: queue.Queue = queue.Queue()
        self._workers: list[BaseWorker] = []
        self._status: dict[str, str] = {}

    def _build_ui(self):
        # Platform frames (YT / TT / TW) with input + start button each
        # Common controls: TTS, volume
        # Chat display with CTkTextbox
        # Status bar per platform

    def _start_platform(self, platform: str):
        # platform in ("YT", "TT", "TW")
        # create appropriate worker, add to self._workers, call start()

    def _stop_all(self):
        for w in self._workers:
            w.stop()

    def _poll_messages(self):
        try:
            while True:
                platform, name, text = self._message_queue.get_nowait()
                if name == "[ระบบ]":
                    self._status[platform] = text
                    self._update_status_bar()
                else:
                    self._display_message(platform, name, text)
                    if self._tts_var.get():
                        self._tts.speak(f"[{platform}] {name}", text)
        except queue.Empty:
            pass
        self.after(100, self._poll_messages)

    def _display_message(self, platform: str, name: str, text: str):
        self._chat_box.configure(state="normal")
        self._chat_box.insert("end", f"[{platform}] {name}: {text}\n")
        self._chat_box.see("end")
        self._chat_box.configure(state="disabled")
```

- [ ] **Step 2: Commit**

```powershell
git add gui.py
git commit -m "feat: redesign GUI for multi-platform input and display"
```

---

### Task 6: Update requirements and clean up

**Files:**
- Modify: `requirements.txt`
- Modify: `agent/Workflow.md`

- [ ] **Step 1: Update requirements**

```powershell
pip freeze > requirements.txt
```

- [ ] **Step 2: Update Workflow.md** — add TikTok + Twitch to diagram

- [ ] **Step 3: Run tests**

```powershell
python -m pytest tests/ -v
```

- [ ] **Step 4: Commit**

```powershell
git add requirements.txt agent/Workflow.md
git commit -m "chore: update deps and workflow diagram for multi-chat"
```
