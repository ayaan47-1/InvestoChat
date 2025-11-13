import os
import re
import time
from collections import defaultdict, deque
from threading import Lock
from typing import Optional, Tuple

BLOCK_TERMS = {
    "password",
    "otp",
    "one time password",
    "credit card",
    "cvv",
    "ssn",
    "aadhaar",
}
PHONE_PATTERN = re.compile(r"\+?\d[\d\s().-]{7,}")
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


class RateLimiter:
    def __init__(self, limit_per_window: int, window_seconds: int):
        self.limit = limit_per_window
        self.window = window_seconds
        self._store = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str) -> Optional[int]:
        """
        Returns None if allowed, else retry-after seconds.
        """
        now = time.time()
        with self._lock:
            bucket = self._store[key]
            while bucket and now - bucket[0] > self.window:
                bucket.popleft()
            if len(bucket) >= self.limit:
                retry_after = int(self.window - (now - bucket[0])) + 1
                return max(retry_after, 1)
            bucket.append(now)
            return None


API_RATE_LIMIT = int(os.getenv("API_RATE_LIMIT", "30"))
WHATSAPP_RATE_LIMIT = int(os.getenv("WHATSAPP_RATE_LIMIT", "12"))
RATE_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

api_rate_limiter = RateLimiter(API_RATE_LIMIT, RATE_WINDOW)
whatsapp_rate_limiter = RateLimiter(WHATSAPP_RATE_LIMIT, RATE_WINDOW)


def guard_question(question: str) -> Tuple[bool, Optional[str]]:
    text = (question or "").strip()
    if not text:
        return False, "question is empty"
    lower = text.lower()
    for term in BLOCK_TERMS:
        if term in lower:
            return False, "I can't help with that request."
    if EMAIL_PATTERN.search(text) or PHONE_PATTERN.search(text):
        return False, "Please avoid sharing personal contact details."
    return True, None
