# supports multi-account cookies, round-robin, basic health/backoff
import os, json, time, threading
from typing import List, Optional
from dataclasses import dataclass, field

@dataclass
class CookieAccount:
    name: str
    path: str
    cookies: list = field(default_factory=list)
    requests_count: int = 0
    disabled_until: float = 0.0
    last_error: str = ""

    def load(self):
        with open(self.path, "r", encoding="utf-8") as f:
            self.cookies = json.load(f)

    def is_available(self):
        return time.time() >= self.disabled_until

    def mark_backoff(self, seconds: int, reason: str):
        self.last_error = reason
        self.disabled_until = time.time() + seconds

class CookiesManager:
    def __init__(self, cookie_paths: List[str], max_requests_per_window: int = 6000, window_seconds: int = 3600):
        self.lock = threading.Lock()
        self.accounts = []
        for p in cookie_paths:
            name = os.path.basename(p)
            acc = CookieAccount(name=name, path=p)
            try:
                acc.load()
            except Exception:
                acc.cookies = []
            self.accounts.append(acc)
        self.idx = 0
        self.max_requests = max_requests_per_window
        self.window_seconds = window_seconds
        self._start_reset_loop()

    def _start_reset_loop(self):
        def loop():
            while True:
                time.sleep(self.window_seconds)
                with self.lock:
                    for a in self.accounts:
                        a.requests_count = 0
        t = threading.Thread(target=loop, daemon=True)
        t.start()

    def get_next(self) -> Optional[CookieAccount]:
        with self.lock:
            n = len(self.accounts)
            if n == 0:
                return None
            for i in range(n):
                acc = self.accounts[(self.idx + i) % n]
                if acc.is_available() and acc.requests_count < self.max_requests and acc.cookies:
                    self.idx = (self.idx + i + 1) % n
                    return acc
            return None

    def increment(self, acc: CookieAccount, n:int =1):
        with self.lock:
            acc.requests_count += n

    def mark_error(self, acc: CookieAccount, backoff_seconds:int=300, reason:str="error"):
        with self.lock:
            acc.mark_backoff(backoff_seconds, reason)
