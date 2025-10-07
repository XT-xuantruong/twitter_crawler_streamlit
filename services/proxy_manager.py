import threading, random
from typing import List, Optional

class ProxyManager:
    def __init__(self, proxies: List[str]):
        self.lock = threading.Lock()
        self.proxies = proxies.copy() if proxies else []
        self.idx = 0

    def get_next(self) -> Optional[str]:
        with self.lock:
            if not self.proxies:
                return None
            p = self.proxies[self.idx % len(self.proxies)]
            self.idx = (self.idx + 1) % len(self.proxies)
            return p

    def get_random(self) -> Optional[str]:
        if not self.proxies:
            return None
        return random.choice(self.proxies)
