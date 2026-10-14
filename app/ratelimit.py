import time
from collections import defaultdict, deque
from threading import Lock

from app.errors import ApiError


class RateLimiter:
    def __init__(self, max_calls: int, window_seconds: int):
        self.max_calls = max_calls
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > self.window:
                hits.popleft()
            if len(hits) >= self.max_calls:
                raise ApiError(
                    429,
                    "RATE_LIMITED",
                    "تعداد درخواست‌ها زیاد است؛ کمی بعد دوباره تلاش کن.",
                )
            hits.append(now)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


# حداکثر ۵ نظر در ساعت برای هر کاربر
review_limiter = RateLimiter(max_calls=5, window_seconds=3600)