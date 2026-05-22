"""Server-side rate limiter using a sliding window algorithm.

Prevents requests from reaching Gemini when we're already over quota.
This is critical for the free tier which allows ~15 requests/minute.
Without this, every request hits the API and gets a 429, wasting
both time and retry budget.

The limiter uses a deque per client IP to track request timestamps
and rejects requests that would exceed the configured limits.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from collections.abc import Callable
from functools import wraps

logger = logging.getLogger("mova.rate_limiter")


class SlidingWindowRateLimiter:
    """Sliding-window rate limiter with per-key buckets.

    For each unique key (e.g. client IP) it tracks request timestamps
    and rejects when the count exceeds the limit within the window.

    Example: 10 requests per 60-second window.
    """

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def check(self, key: str) -> tuple[bool, int]:
        """Check if a request from `key` is allowed.

        Returns (True, 0) if under the limit,
        or (False, retry_after_seconds) if rate-limited.
        """
        now = time.monotonic()
        cutoff = now - self.window_seconds

        async with self._lock:
            timestamps = self._buckets[key]
            self._buckets[key] = [t for t in timestamps if t > cutoff]
            bucket = self._buckets[key]

            if len(bucket) >= self.max_requests:
                oldest = bucket[0]
                wait = int(self.window_seconds - (now - oldest))
                logger.warning("Rate-limited key=%s wait=%ds count=%d", key, wait, len(bucket))
                return False, wait

            bucket.append(now)
            return True, 0

    def get_remaining(self, key: str) -> int:
        """How many more requests this key can make before being limited."""
        now = time.monotonic()
        cutoff = now - self.window_seconds
        timestamps = [t for t in self._buckets.get(key, []) if t > cutoff]
        return max(0, self.max_requests - len(timestamps))


# Singleton
rate_limiter = SlidingWindowRateLimiter(max_requests=10, window_seconds=60)
