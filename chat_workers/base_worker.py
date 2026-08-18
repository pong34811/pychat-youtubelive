from abc import ABC, abstractmethod
import queue
import threading
import logging

logger = logging.getLogger(__name__)

class BaseWorker(ABC):
    def __init__(self, message_queue: queue.Queue) -> None:
        self.message_queue = message_queue
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    @abstractmethod
    def _run(self) -> None:
        ...

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
            logger.debug("Worker thread joined")

    @property
    def is_alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive()
