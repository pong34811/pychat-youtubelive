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

    def _run(self) -> None:
        try:
            chat = pytchat.create(video_id=self.video_id)
        except Exception as e:
            self.message_queue.put((PLATFORM, "[ระบบ]", f"❌ YouTube: {e}"))
            return

        while not self._stop_event.is_set() and chat.is_alive():
            try:
                items = chat.get().sync_items()
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
