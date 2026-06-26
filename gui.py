import queue
import threading
from typing import Optional

import customtkinter as ctk

from chat_workers import YouTubeWorker, TikTokWorker, TwitchWorker
from main import get_video_id
from tts_handler import TTSHandler


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


class ChatGUI(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.title("PyChat YouTube Live")
        self.geometry("750x600")
        self.minsize(500, 400)

        self._message_queue: queue.Queue = queue.Queue()
        self._tts = TTSHandler()
        self._tts.start()

        self._workers: list = []
        self._platform_status: dict[str, str] = {}

        self._build_ui()
        self.after(100, self._poll_messages)

    def _build_ui(self) -> None:
        # --- YouTube ---
        yt_frame = ctk.CTkFrame(self, fg_color="transparent")
        yt_frame.pack(fill="x", padx=10, pady=(10, 2))

        ctk.CTkLabel(yt_frame, text="▶ YouTube", width=80).pack(side="left")
        self._yt_entry = ctk.CTkEntry(
            yt_frame, placeholder_text="URL หรือ video id"
        )
        self._yt_entry.pack(side="left", fill="x", expand=True, padx=5)
        self._yt_btn = ctk.CTkButton(
            yt_frame, text="Start", command=lambda: self._start_platform("YT"),
            width=60
        )
        self._yt_btn.pack(side="right")

        # --- TikTok ---
        tt_frame = ctk.CTkFrame(self, fg_color="transparent")
        tt_frame.pack(fill="x", padx=10, pady=2)

        ctk.CTkLabel(tt_frame, text="♫ TikTok", width=80).pack(side="left")
        self._tt_entry = ctk.CTkEntry(
            tt_frame, placeholder_text="@username"
        )
        self._tt_entry.pack(side="left", fill="x", expand=True, padx=5)
        self._tt_btn = ctk.CTkButton(
            tt_frame, text="Start", command=lambda: self._start_platform("TT"),
            width=60
        )
        self._tt_btn.pack(side="right")

        # --- Twitch ---
        tw_frame = ctk.CTkFrame(self, fg_color="transparent")
        tw_frame.pack(fill="x", padx=10, pady=2)

        ctk.CTkLabel(tw_frame, text="⚡ Twitch", width=80).pack(side="left")
        self._tw_entry = ctk.CTkEntry(
            tw_frame, placeholder_text="#channel"
        )
        self._tw_entry.pack(side="left", fill="x", expand=True, padx=5)
        self._tw_btn = ctk.CTkButton(
            tw_frame, text="Start", command=lambda: self._start_platform("TW"),
            width=60
        )
        self._tw_btn.pack(side="right")

        # --- Controls ---
        ctrl_frame = ctk.CTkFrame(self, fg_color="transparent")
        ctrl_frame.pack(fill="x", padx=10, pady=5)

        self._stop_all_btn = ctk.CTkButton(
            ctrl_frame, text="⏹ Stop All", command=self._stop_all,
            width=80, fg_color="#c0392b"
        )
        self._stop_all_btn.pack(side="left", padx=(0, 10))

        self._tts_var = ctk.BooleanVar(value=True)
        self._tts_check = ctk.CTkCheckBox(
            ctrl_frame, text="🔊 TTS", variable=self._tts_var
        )
        self._tts_check.pack(side="left", padx=5)

        self._volume_var = ctk.DoubleVar(value=50)
        self._volume_slider = ctk.CTkSlider(
            ctrl_frame, from_=0, to=100,
            variable=self._volume_var, width=100,
            command=self._on_volume_change,
        )
        self._volume_slider.set(50)
        self._volume_slider.pack(side="left", padx=5)

        self._volume_label = ctk.CTkLabel(ctrl_frame, text="🔊 50%")
        self._volume_label.pack(side="left")

        # --- Chat Display ---
        self._chat_box = ctk.CTkTextbox(self, wrap="word", state="disabled")
        self._chat_box.pack(fill="both", expand=True, padx=10, pady=5)

        # --- Status Bar ---
        self._status_label = ctk.CTkLabel(
            self, text="✅ พร้อมทำงาน", anchor="w"
        )
        self._status_label.pack(fill="x", padx=10, pady=(0, 10))

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _start_platform(self, platform: str) -> None:
        if platform == "YT":
            url = self._yt_entry.get().strip()
            if not url:
                self._set_status("⚠️ กรุณาใส่ URL YouTube")
                return
            video_id = get_video_id(url)
            worker = YouTubeWorker(video_id, self._message_queue)
            self._yt_btn.configure(state="disabled")
        elif platform == "TT":
            username = self._tt_entry.get().strip()
            if not username:
                self._set_status("⚠️ กรุณาใส่ TikTok username")
                return
            worker = TikTokWorker(username, self._message_queue)
            self._tt_btn.configure(state="disabled")
        elif platform == "TW":
            channel = self._tw_entry.get().strip()
            if not channel:
                self._set_status("⚠️ กรุณาใส่ Twitch channel")
                return
            worker = TwitchWorker(channel, self._message_queue)
            self._tw_btn.configure(state="disabled")
        else:
            return

        worker.start()
        self._workers.append(worker)
        self._set_status(f"⏳ {platform} กำลังเชื่อมต่อ...")

    def _stop_all(self) -> None:
        for w in self._workers:
            w.stop()
        self._workers.clear()
        self._yt_btn.configure(state="normal")
        self._tt_btn.configure(state="normal")
        self._tw_btn.configure(state="normal")
        self._set_status("⏹ หยุดทั้งหมดแล้ว")

    def _poll_messages(self) -> None:
        try:
            while True:
                platform, name, text = self._message_queue.get_nowait()
                if name == "[ระบบ]":
                    self._platform_status[platform] = text
                    self._update_status()
                else:
                    self._display_message(platform, name, text)
                    if self._tts_var.get():
                        self._tts.speak(f"[{platform}] {name}", text)
        except queue.Empty:
            pass
        self.after(100, self._poll_messages)

    def _display_message(self, platform: str, name: str, text: str) -> None:
        color_map = {"YT": "#FF0000", "TT": "#00FF00", "TW": "#9147FF"}
        color = color_map.get(platform, "#FFFFFF")

        self._chat_box.configure(state="normal")
        self._chat_box.insert("end", f"[{platform}] ", "platform_tag")
        self._chat_box.insert("end", f"{name}: {text}\n")
        self._chat_box.see("end")
        self._chat_box.configure(state="disabled")

    def _update_status(self) -> None:
        parts = []
        for p, s in self._platform_status.items():
            parts.append(f"[{p}] {s}")
        self._status_label.configure(text=" | ".join(parts) if parts else "✅ พร้อมทำงาน")

    def _set_status(self, text: str) -> None:
        self._status_label.configure(text=text)

    def _on_volume_change(self, value: float) -> None:
        volume = int(value)
        self._volume_label.configure(text=f"🔊 {volume}%")
        self._tts.set_volume(volume / 100)

    def _on_close(self) -> None:
        self._stop_all()
        self._tts.stop()
        self.destroy()


if __name__ == "__main__":
    app = ChatGUI()
    app.mainloop()
