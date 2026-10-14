import time
import queue
import logging
import threading
from typing import Any

import httpx
import pytchat

from fix_message import sanitize_message
from .base_worker import BaseWorker


PLATFORM = "YT"
INITIAL_BACKOFF = 3  # seconds
MAX_BACKOFF = 60     # seconds
GET_ITEMS_TIMEOUT = 60  # seconds — force reconnect when poll blocks this long
MAX_EMPTY_POLLS = 10    # empty polls before forcing reconnect

logger = logging.getLogger(__name__)


class YouTubeWorker(BaseWorker):
    def __init__(self, video_id: str, message_queue: queue.Queue) -> None:
        super().__init__(message_queue)
        self.video_id = video_id
        self._chat: Any = None

    def create_chat(self) -> str | None:
        try:
            self._chat = pytchat.create(video_id=self.video_id, interruptable=False)
            return None
        except Exception as e:
            return str(e)

    # ------------------------------------------------------------------
    # Timeout-safe wrapper for chat.get().sync_items()
    # When the YouTube stream dies, chat.get() can block forever because
    # pytchat's internal thread keeps running (is_alive() == True) but no
    # new messages arrive.  We run the call in a daemon thread so we can
    # abandon it after GET_ITEMS_TIMEOUT seconds.
    # ------------------------------------------------------------------
    @staticmethod
    def _get_chat_items(chat: Any, timeout: float = GET_ITEMS_TIMEOUT) -> list:
        result_q: queue.Queue = queue.Queue()

        def _fetch() -> None:
            try:
                result_q.put(chat.get().sync_items())
            except Exception:
                result_q.put([])

        t = threading.Thread(target=_fetch, daemon=True)
        t.start()
        try:
            return result_q.get(timeout=timeout)
        except queue.Empty:
            logger.warning("chat.get() blocked for %.0fs — stream likely dead", timeout)
            return []

    def _run(self) -> None:
        # NOTE: retries reset is now handled inside _reconnect()
        if not self._chat:
            self.message_queue.put((PLATFORM, "[ระบบ]", "❌ YouTube: chat not created"))
            return

        chat = self._chat
        self.message_queue.put((PLATFORM, "[ระบบ]", "✅ YouTube connected"))
        retries = 0

        while not self._stop_event.is_set():
            try:
                # --- inner polling loop ---
                empty_polls = 0
                while not self._stop_event.is_set() and chat.is_alive():
                    items = self._get_chat_items(chat)

                    if items:
                        empty_polls = 0  # reset on real data
                        for c in items:
                            if self._stop_event.is_set():
                                return
                            clean = sanitize_message(c.message)
                            if not clean:
                                continue
                            self.message_queue.put((PLATFORM, c.author.name, clean))
                    else:
                        empty_polls += 1
                        if empty_polls >= MAX_EMPTY_POLLS:
                            logger.warning(
                                "Stream stale: %d empty polls while is_alive=True — forcing reconnect",
                                empty_polls,
                            )
                            break  # → outer loop reconnects

                # --- chat died or stale → try reconnect ---
                if self._stop_event.is_set():
                    return

                retries = self._reconnect(retries, chat)
                if retries is None:          # stopped by user
                    return
                chat = self._chat            # refreshed by _reconnect

            except Exception as e:
                # Catch-all: network errors, JSON decode errors, etc.
                if self._stop_event.is_set():
                    return

                retries += 1
                backoff = min(INITIAL_BACKOFF * (2 ** (retries - 1)), MAX_BACKOFF)
                self.message_queue.put(
                    (PLATFORM, "[ระบบ]", f"⚠️ YouTube error: {e} — retry {retries} (รอ {backoff}s)")
                )
                logger.warning("YouTube worker error (attempt %d): %s", retries, e)

                if self._stop_event.wait(timeout=backoff):
                    return

                # Try to recreate chat after unexpected error
                try:
                    chat = pytchat.create(video_id=self.video_id, interruptable=False)
                    self._chat = chat
                except Exception:
                    continue  # re-enter inner loop to test new chat

        self.message_queue.put((PLATFORM, "[ระบบ]", "⏹ YouTube stopped"))

    def _reconnect(self, retries: int, old_chat: Any) -> int | None:
        """Attempt to reconnect the pytchat session.

        Returns the updated retry counter, or ``None`` if the worker was
        stopped while waiting.
        """
        retries += 1
        backoff = min(INITIAL_BACKOFF * (2 ** (retries - 1)), MAX_BACKOFF)
        self.message_queue.put(
            (PLATFORM, "[ระบบ]", f"🔄 YouTube chat หมดอายุ — reconnect ครั้งที่ {retries} (รอ {backoff}s)")
        )
        logger.warning("pytchat session expired, reconnecting (attempt %d)", retries)

        if self._stop_event.wait(timeout=backoff):
            return None

        try:
            chat = pytchat.create(video_id=self.video_id, interruptable=False)
            self._chat = chat
            retries = 0  # reset on successful reconnect
            self.message_queue.put((PLATFORM, "[ระบบ]", "✅ YouTube reconnected"))
            logger.info("pytchat reconnected successfully")
        except Exception as e:
            logger.error("pytchat reconnect failed: %s", e)
            # will loop back and retry

        return retries
