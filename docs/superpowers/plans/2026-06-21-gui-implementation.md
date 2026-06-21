# GUI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a modern GUI window to replace the CLI chat reader, with URL input, start/stop, chat display, TTS toggle, and status bar.

**Architecture:** `gui.py` runs its own background chat thread (using pytchat + sanitize_message + TTSHandler) and communicates with the GUI via `queue.Queue`. Main thread polls the queue every 100ms to display messages. `main.py` CLI stays untouched.

**Tech Stack:** Python 3.9+, customtkinter, threading, queue

## Global Constraints

- Python 3.9+
- Type hints all functions
- User-facing text in Thai
- GUI must never freeze (chat in background thread)
- TTS toggle without modifying tts_handler.py
- Separate file from main.py (keep CLI working)

---

### Task 1: Install customtkinter and update requirements

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Install customtkinter**

Run:
```powershell
pip install customtkinter
```

- [ ] **Step 2: Update requirements.txt**

Run:
```powershell
pip freeze > requirements.txt
```

- [ ] **Step 3: Commit**

```powershell
git add requirements.txt
git commit -m "chore: add customtkinter dependency"
```

---

### Task 2: Create `gui.py` — GUI Application

**Files:**
- Create: `gui.py`

**Interfaces:**
- Consumes: `get_video_id` from `main.py`, `sanitize_message` from `fix_message.py`, `TTSHandler` from `tts_handler.py`
- Produces: standalone GUI application runnable via `python gui.py`

- [ ] **Step 1: Write gui.py**

```python
# gui.py
import queue
import threading
import time
from typing import Optional

import customtkinter as ctk
import httpx
import pytchat

from fix_message import sanitize_message
from main import get_video_id
from tts_handler import TTSHandler


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


class ChatGUI(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.title("PyChat YouTube Live")
        self.geometry("700x500")
        self.minsize(500, 400)

        self._chat_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._message_queue: queue.Queue = queue.Queue()
        self._tts = TTSHandler()
        self._tts.start()

        self._build_ui()
        self.after(100, self._poll_messages)

    def _build_ui(self) -> None:
        # URL input row
        self._url_entry = ctk.CTkEntry(
            self, placeholder_text="วางลิงก์ YouTube Live หรือ video id"
        )
        self._url_entry.pack(fill="x", padx=10, pady=(10, 5))

        # Control row
        control_frame = ctk.CTkFrame(self, fg_color="transparent")
        control_frame.pack(fill="x", padx=10, pady=5)

        self._start_btn = ctk.CTkButton(
            control_frame, text="▶ Start", command=self._start_chat, width=80
        )
        self._start_btn.pack(side="left", padx=(0, 5))

        self._stop_btn = ctk.CTkButton(
            control_frame,
            text="⏹ Stop",
            command=self._stop_chat,
            width=80,
            state="disabled",
        )
        self._stop_btn.pack(side="left", padx=5)

        self._tts_var = ctk.BooleanVar(value=True)
        self._tts_check = ctk.CTkCheckBox(
            control_frame, text="🔊 TTS", variable=self._tts_var
        )
        self._tts_check.pack(side="left", padx=5)

        # Chat display
        self._chat_box = ctk.CTkTextbox(self, wrap="word", state="disabled")
        self._chat_box.pack(fill="both", expand=True, padx=10, pady=5)

        # Status bar
        self._status_label = ctk.CTkLabel(
            self, text="✅ พร้อมทำงาน", anchor="w"
        )
        self._status_label.pack(fill="x", padx=10, pady=(0, 10))

        # Bind close event
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _start_chat(self) -> None:
        url = self._url_entry.get().strip()
        if not url:
            self._set_status("⚠️ กรุณาใส่ลิงก์หรือ video id")
            return

        video_id = get_video_id(url)
        self._set_status(f"⏳ กำลังเชื่อมต่อ...")
        self._start_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")
        self._url_entry.configure(state="disabled")

        self._stop_event.clear()
        self._chat_thread = threading.Thread(
            target=self._chat_loop, args=(video_id,), daemon=True
        )
        self._chat_thread.start()

    def _stop_chat(self) -> None:
        self._stop_event.set()
        self._start_btn.configure(state="normal")
        self._stop_btn.configure(state="disabled")
        self._url_entry.configure(state="normal")
        self._set_status("⏹ หยุดแล้ว")

    def _chat_loop(self, video_id: str) -> None:
        try:
            chat = pytchat.create(video_id=video_id)
        except Exception:
            self._message_queue.put(("_system", "❌ ไม่สามารถเชื่อมต่อแชตได้"))
            return

        while not self._stop_event.is_set() and chat.is_alive():
            try:
                items = chat.get().sync_items()
            except httpx.ReadTimeout:
                self._message_queue.put(("_system", "เชื่อมต่อช้า กำลังลองใหม่..."))
                time.sleep(3)
                continue

            for c in items:
                if self._stop_event.is_set():
                    return
                clean_message = sanitize_message(c.message)
                if not clean_message:
                    continue
                self._message_queue.put((c.author.name, clean_message))

        if not self._stop_event.is_set():
            self._message_queue.put(("_system", "📴 แชตจบลงแล้ว"))

    def _poll_messages(self) -> None:
        try:
            while True:
                name, text = self._message_queue.get_nowait()
                if name == "_system":
                    self._set_status(text)
                else:
                    self._display_message(name, text)
                    if self._tts_var.get():
                        self._tts.speak(name, text)
        except queue.Empty:
            pass
        self.after(100, self._poll_messages)

    def _display_message(self, name: str, text: str) -> None:
        self._chat_box.configure(state="normal")
        self._chat_box.insert("end", f"{name}: {text}\n")
        self._chat_box.see("end")
        self._chat_box.configure(state="disabled")

    def _set_status(self, text: str) -> None:
        self._status_label.configure(text=text)

    def _on_close(self) -> None:
        self._stop_event.set()
        self._tts.stop()
        self.destroy()


if __name__ == "__main__":
    app = ChatGUI()
    app.mainloop()
```

- [ ] **Step 2: Run the GUI to verify it opens**

```powershell
python gui.py
```
Expected: GUI window opens with dark theme, URL input, Start/Stop buttons, TTS checkbox, chat area, status bar

- [ ] **Step 3: Commit**

```powershell
git add gui.py
git commit -m "feat: add GUI application with customtkinter"
```
