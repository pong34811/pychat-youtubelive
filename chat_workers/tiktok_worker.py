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
