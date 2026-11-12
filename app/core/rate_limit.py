"""In-memory sliding window rate limiter."""

# Standard library
import threading
import time
from collections import deque

# Project imports
from app.core.errors import RateLimitError


class SlidingWindowLimiter:
    """Count requests per key inside a rolling window."""

    def __init__(self, limit: int, window_seconds: int = 60) -> None:
        if limit <= 0:
            raise ValueError("The limit must be positive")
        self._limit: int = limit
        self._window_seconds: int = window_seconds
        self._events: dict[str, deque[float]] = {}
        self._guard: threading.Lock = threading.Lock()

    def check(self, key: str) -> None:
        """Register a hit for the key or raise a rate limit error."""
        now = time.monotonic()
        threshold = now - self._window_seconds
        with self._guard:
            events = self._events.setdefault(key, deque())
            while events and events[0] <= threshold:
                events.popleft()
            if len(events) >= self._limit:
                retry_after = max(1, int(events[0] + self._window_seconds - now) + 1)
                raise RateLimitError(retry_after)
            events.append(now)

    def reset(self) -> None:
        """Drop every recorded event, used by tests."""
        with self._guard:
            self._events.clear()
