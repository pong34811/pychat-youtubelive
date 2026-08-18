import time
import queue
import logging
from typing import Any

import httpx
import pytchat

from fix_message import sanitize_message
from .base_worker import BaseWorker


PLATFORM = "YT"
MAX_RETRIES = 10
INITIAL_BACKOFF = 3  # seconds
MAX_BACKOFF = 60     # seconds

logger = logging.getLogger(__name__)


class YouTubeWorker(BaseWorker):
    def __init__(self, video_id: str, message_queue: queue.Queue) -> None:
        super().__init__(message_queue)
        self.video_id = video_id
        self._chat: Any = None

    def create_chat(self) -> str | None:
        try:
            self._chat = pytchat.create(video_id=self.video_id)
            return None
        except Exception as e:
            return str(e)

    def _run(self) -> None:
        if not self._chat:
            self.message_queue.put((PLATFORM, "[ระบบ]", "❌ YouTube: chat not created"))
            return

        chat = self._chat
        self.message_queue.put((PLATFORM, "[ระบบ]", "✅ YouTube connected"))
        retries = 0

        while not self._stop_event.is_set():
            try:
                # --- inner polling loop ---
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

                    # Reset retries on successful poll
                    retries = 0

                # --- chat.is_alive() returned False → try reconnect ---
                if self._stop_event.is_set():
                    return

                retries += 1
                if retries >= MAX_RETRIES:
                    self.message_queue.put(
                        (PLATFORM, "[ระบบ]", f"❌ YouTube reconnect failed {MAX_RETRIES} ครั้ง — หยุดทำงาน")
                    )
                    return

                backoff = min(INITIAL_BACKOFF * (2 ** (retries - 1)), MAX_BACKOFF)
                self.message_queue.put(
                    (PLATFORM, "[ระบบ]", f"🔄 YouTube chat หมดอายุ — reconnect ครั้งที่ {retries}/{MAX_RETRIES} (รอ {backoff}s)")
                )
                logger.warning("pytchat session expired, reconnecting (attempt %d)", retries)

                # Wait with stop-event awareness
                if self._stop_event.wait(timeout=backoff):
                    return

                try:
                    chat = pytchat.create(video_id=self.video_id)
                    self._chat = chat
                    self.message_queue.put((PLATFORM, "[ระบบ]", "✅ YouTube reconnected"))
                    logger.info("pytchat reconnected successfully")
                except Exception as e:
                    logger.error("pytchat reconnect failed: %s", e)
                    # will loop back and retry

            except Exception as e:
                # Catch-all: network errors, JSON decode errors, etc.
                if self._stop_event.is_set():
                    return

                retries += 1
                if retries >= MAX_RETRIES:
                    self.message_queue.put(
                        (PLATFORM, "[ระบบ]", f"❌ YouTube error — หยุดทำงาน: {e}")
                    )
                    logger.exception("YouTube worker giving up after %d retries", MAX_RETRIES)
                    return

                backoff = min(INITIAL_BACKOFF * (2 ** (retries - 1)), MAX_BACKOFF)
                self.message_queue.put(
                    (PLATFORM, "[ระบบ]", f"⚠️ YouTube error: {e} — retry {retries}/{MAX_RETRIES} (รอ {backoff}s)")
                )
                logger.warning("YouTube worker error (attempt %d): %s", retries, e)

                if self._stop_event.wait(timeout=backoff):
                    return

                # Try to recreate chat after unexpected error
                try:
                    chat = pytchat.create(video_id=self.video_id)
                    self._chat = chat
                except Exception:
                    pass  # will loop back and retry

        self.message_queue.put((PLATFORM, "[ระบบ]", "⏹ YouTube stopped"))
