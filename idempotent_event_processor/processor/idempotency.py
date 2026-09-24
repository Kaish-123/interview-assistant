import threading
import time
from typing import Dict


class IdempotencyStore:
    def __init__(self, ttl_seconds: int = 300):
        self.ttl_seconds = ttl_seconds
        self._store: Dict[str, float] = {}
        self._lock = threading.Lock()

    def is_duplicate(self, event_id: str) -> bool:
        with self._lock:
            expiry = self._store.get(event_id)
            if expiry and expiry > time.time():
                return True
            return False

    def mark_seen(self, event_id: str) -> None:
        with self._lock:
            self._store[event_id] = time.time() + self.ttl_seconds
