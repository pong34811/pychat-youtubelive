import asyncio
import queue
import time

from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent, ConnectEvent, DisconnectEvent

from fix_message import sanitize_message
from .base_worker import BaseWorker


PLATFORM = "TT"
SKIP_SECONDS = 5


class TikTokWorker(BaseWorker):
    def __init__(self, username: str, message_queue: queue.Queue) -> None:
        super().__init__(message_queue)
        self.username = username.strip("@")
        self._connected_at: float = 0

    def _run(self) -> None:
        async def _connect():
            client = TikTokLiveClient(unique_id=self.username)

            @client.on(ConnectEvent)
            async def on_connect(_):
                self._connected_at = time.time()
                self.message_queue.put((PLATFORM, "[ระบบ]", "✅ TikTok connected"))

            @client.on(DisconnectEvent)
            async def on_disconnect(_):
                self.message_queue.put((PLATFORM, "[ระบบ]", "🔌 TikTok disconnected"))

            @client.on(CommentEvent)
            async def on_comment(event: CommentEvent):
                if self._stop_event.is_set():
                    await client.disconnect()
                    return
                if time.time() - self._connected_at < SKIP_SECONDS:
                    return
                text = sanitize_message(event.comment)
                if text:
                    self.message_queue.put((PLATFORM, event.user.unique_id, text))

            try:
                task = asyncio.create_task(client.start())
                while not self._stop_event.is_set():
                    if task.done():
                        exc = task.exception()
                        if exc:
                            self.message_queue.put((PLATFORM, "[ระบบ]", f"❌ TikTok: {exc}"))
                        break
                    await asyncio.sleep(1)
            except Exception as e:
                self.message_queue.put((PLATFORM, "[ระบบ]", f"❌ TikTok: {e}"))
            finally:
                try:
                    await client.disconnect()
                except Exception:
                    pass

        asyncio.run(_connect())
