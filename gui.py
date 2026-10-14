import queue
import threading
from typing import Optional

import customtkinter as ctk

from chat_workers import get_worker
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
        self._tts = TTSHandler(message_queue=self._message_queue)
        self._tts.start()

        # Track workers per platform (at most one per platform)
        self._workers: dict[str, object] = {}
        self._platform_ids: dict[str, str] = {}
        self._platform_status: dict[str, str] = {}
        self._reconnect_counts: dict[str, int] = {}

        self._build_ui()
        self.after(100, self._poll_messages)
        self.after(5000, self._health_check)

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
            yt_frame, text="Start", command=lambda: self._toggle_platform("YT"),
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
        self._tt_entry.insert(0, "@katy404_vtuberth")
        self._tt_entry.pack(side="left", fill="x", expand=True, padx=5)
        self._tt_btn = ctk.CTkButton(
            tt_frame, text="Start", command=lambda: self._toggle_platform("TT"),
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
        self._tw_entry.insert(0, "kaynavtuberth")
        self._tw_entry.pack(side="left", fill="x", expand=True, padx=5)
        self._tw_btn = ctk.CTkButton(
            tw_frame, text="Start", command=lambda: self._toggle_platform("TW"),
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

    # --- helpers to map platform to button/entry ---

    def _get_btn(self, platform: str) -> ctk.CTkButton:
        return {"YT": self._yt_btn, "TT": self._tt_btn, "TW": self._tw_btn}[platform]

    def _get_entry(self, platform: str) -> ctk.CTkEntry:
        return {"YT": self._yt_entry, "TT": self._tt_entry, "TW": self._tw_entry}[platform]

    # --- toggle Start / Stop per platform ---

    def _toggle_platform(self, platform: str) -> None:
        if platform in self._workers:
            self._stop_platform(platform)
        else:
            self._start_platform(platform)

    def _create_worker(self, platform: str, identifier: str):
        """Create and initialize a worker. Returns (worker, error_string_or_None)."""
        try:
            worker = get_worker(platform, identifier, self._message_queue)
        except Exception as e:
            return None, str(e)
        if platform == "YT":
            err = worker.create_chat()
            if err:
                return None, err
        return worker, None

    def _start_platform(self, platform: str) -> None:
        entry = self._get_entry(platform)
        identifier = entry.get().strip()

        if platform == "YT":
            if not identifier:
                self._set_status("⚠️ กรุณาใส่ URL YouTube")
                return
            identifier = get_video_id(identifier)
        elif platform == "TT":
            if not identifier:
                self._set_status("⚠️ กรุณาใส่ TikTok username")
                return
        elif platform == "TW":
            if not identifier:
                self._set_status("⚠️ กรุณาใส่ Twitch channel")
                return
        else:
            return

        worker, err = self._create_worker(platform, identifier)
        if err:
            self._set_status(f"❌ {platform}: {err}")
            return

        worker.start()
        self._workers[platform] = worker
        self._platform_ids[platform] = identifier

        btn = self._get_btn(platform)
        btn.configure(text="Stop", fg_color="#c0392b", hover_color="#922b21")
        self._set_status(f"⏳ {platform} กำลังเชื่อมต่อ...")

    def _stop_platform(self, platform: str) -> None:
        worker = self._workers.pop(platform, None)
        if worker:
            worker.stop()

        self._platform_ids.pop(platform, None)
        btn = self._get_btn(platform)
        btn.configure(text="Start", fg_color=("#2CC985", "#2FA572"), hover_color=("#0C955A", "#106A43"))

        self._platform_status.pop(platform, None)
        self._reconnect_counts.pop(platform, None)
        self._update_status()
        self._set_status(f"⏹ {platform} หยุดแล้ว")

    def _stop_all(self) -> None:
        for platform in list(self._workers.keys()):
            self._stop_platform(platform)
        self._set_status("⏹ หยุดทั้งหมดแล้ว")

    # --- health check: detect dead worker threads ---

    def _health_check(self) -> None:
        dead_platforms = []
        for platform, worker in list(self._workers.items()):
            if not worker.is_alive:
                dead_platforms.append(platform)

        for platform in dead_platforms:
            self._workers.pop(platform, None)
            identifier = self._platform_ids.get(platform)
            if identifier:
                worker, err = self._create_worker(platform, identifier)
                if err:
                    self._platform_status[platform] = f"❌ auto-restart failed: {err}"
                else:
                    worker.start()
                    self._workers[platform] = worker
                    self._platform_status[platform] = "🔄 auto-restarted"
                    self._reconnect_counts[platform] = 0
                    logger.info("Auto-restarted %s worker (id=%s)", platform, identifier)
            else:
                self._platform_status[platform] = "📴 disconnected"

        if dead_platforms:
            self._update_status()

        self.after(5000, self._health_check)

    def _poll_messages(self) -> None:
        try:
            while True:
                platform, name, text = self._message_queue.get_nowait()
                if name == "[ระบบ]":
                    self._platform_status[platform] = text
                    self._track_reconnect(platform, text)
                    self._update_status()
                elif platform == "TTS":
                    self._display_message(platform, name, text)
                else:
                    self._display_message(platform, name, text)
                    if self._tts_var.get():
                        self._tts.speak(name, text)
        except queue.Empty:
            pass
        self.after(100, self._poll_messages)

    def _track_reconnect(self, platform: str, text: str) -> None:
        """Track reconnect attempts from worker status messages."""
        if text.startswith("🔄"):
            # Reconnect attempt — increment counter
            self._reconnect_counts[platform] = self._reconnect_counts.get(platform, 0) + 1
        elif "reconnected" in text.lower() or "connected" in text.lower():
            # Successful reconnect or fresh connect — reset counter
            self._reconnect_counts[platform] = 0

    def _display_message(self, platform: str, name: str, text: str) -> None:
        icon_map = {"YT": "▶️", "TT": "🎵", "TW": "🎮"}
        icon = icon_map.get(platform, platform)

        self._chat_box.configure(state="normal")
        self._chat_box.insert("end", f"{icon} {name}: {text}\n")
        self._chat_box.see("end")
        self._chat_box.configure(state="disabled")

    def _update_status(self) -> None:
        icon_map = {"YT": "▶️", "TT": "🎵", "TW": "🎮"}
        parts = []
        for p, s in self._platform_status.items():
            icon = icon_map.get(p, p)
            count = self._reconnect_counts.get(p, 0)
            if count > 0:
                parts.append(f"{icon} {s}  🔄×{count}")
            else:
                parts.append(f"{icon} {s}")
        self._status_label.configure(
            text=" | ".join(parts) if parts else "✅ พร้อมทำงาน"
        )

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
