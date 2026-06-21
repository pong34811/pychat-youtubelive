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
        self._url_entry = ctk.CTkEntry(
            self, placeholder_text="วางลิงก์ YouTube Live หรือ video id"
        )
        self._url_entry.pack(fill="x", padx=10, pady=(10, 5))

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

        self._volume_var = ctk.DoubleVar(value=50)
        self._volume_slider = ctk.CTkSlider(
            control_frame,
            from_=0,
            to=100,
            variable=self._volume_var,
            width=100,
            command=self._on_volume_change,
        )
        self._volume_slider.set(50)
        self._volume_slider.pack(side="left", padx=5)

        self._volume_label = ctk.CTkLabel(control_frame, text="🔊 50%")
        self._volume_label.pack(side="left", padx=(0, 5))

        self._chat_box = ctk.CTkTextbox(self, wrap="word", state="disabled")
        self._chat_box.pack(fill="both", expand=True, padx=10, pady=5)

        self._status_label = ctk.CTkLabel(
            self, text="✅ พร้อมทำงาน", anchor="w"
        )
        self._status_label.pack(fill="x", padx=10, pady=(0, 10))

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _start_chat(self) -> None:
        url = self._url_entry.get().strip()
        if not url:
            self._set_status("⚠️ กรุณาใส่ลิงก์หรือ video id")
            return

        video_id = get_video_id(url)
        self._set_status("⏳ กำลังเชื่อมต่อ...")

        try:
            chat = pytchat.create(video_id=video_id)
        except Exception as e:
            self._set_status(f"❌ ไม่สามารถเชื่อมต่อแชตได้: {e}")
            return

        self._start_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")
        self._url_entry.configure(state="disabled")

        self._stop_event.clear()
        self._chat_thread = threading.Thread(
            target=self._chat_loop, args=(chat,), daemon=True
        )
        self._chat_thread.start()

    def _stop_chat(self) -> None:
        self._stop_event.set()
        self._start_btn.configure(state="normal")
        self._stop_btn.configure(state="disabled")
        self._url_entry.configure(state="normal")
        self._set_status("⏹ หยุดแล้ว")

    def _chat_loop(self, chat) -> None:
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

    def _on_volume_change(self, value: float) -> None:
        volume = int(value)
        self._volume_label.configure(text=f"🔊 {volume}%")
        self._tts.set_volume(volume / 100)

    def _on_close(self) -> None:
        self._stop_event.set()
        self._tts.stop()
        self.destroy()


if __name__ == "__main__":
    app = ChatGUI()
    app.mainloop()
