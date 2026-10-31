"""Bounded in-process rate limiting for public model-backed requests."""

from collections import deque
from threading import Lock
from time import monotonic


class RateLimiter:
    def __init__(self, per_owner=12, total=120, window=60):
        self.per_owner = per_owner
        self.total = total
        self.window = window
        self.events = deque()
        self.lock = Lock()

    def allow(self, owner):
        with self.lock:
            now = monotonic()
            while self.events and now - self.events[0][0] >= self.window:
                self.events.popleft()
            if (
                len(self.events) >= self.total
                or sum(key == owner for _, key in self.events) >= self.per_owner
            ):
                return False
            self.events.append((now, owner))
            return True
