"""Worker registry and factory for pychat-youtubelive.
Provides a mapping from platform codes to concrete worker classes and a helper
function to instantiate the appropriate worker.
"""

from .youtube_worker import YouTubeWorker
from .tiktok_worker import TikTokWorker
from .twitch_worker import TwitchWorker

# Mapping platform identifiers to worker classes
WORKER_MAP = {
    "YT": YouTubeWorker,
    "TT": TikTokWorker,
    "TW": TwitchWorker,
}

def get_worker(platform: str, identifier: str, queue_obj):
    """Factory returning an instantiated worker.
    * ``platform`` – one of "YT", "TT", "TW".
    * ``identifier`` – video id, username, or channel name.
    * ``queue_obj`` – shared ``queue.Queue`` instance.
    Raises ``ValueError`` for unsupported platforms.
    """
    worker_cls = WORKER_MAP.get(platform)
    if not worker_cls:
        raise ValueError(f"Unsupported platform: {platform}")
    return worker_cls(identifier, queue_obj)
