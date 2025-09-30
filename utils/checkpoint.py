import os, json
from typing import List, Set

class Checkpoint:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.data = {"seen_ids": []}
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {"seen_ids": []}

    def add_seen(self, ids: List[str]):
        seen: Set[str] = set(self.data.get("seen_ids", []))
        seen.update([i for i in ids if i])
        self.data["seen_ids"] = list(seen)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
