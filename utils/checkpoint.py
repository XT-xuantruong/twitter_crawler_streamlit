import os, json
from typing import Optional, List

class Checkpoint:
    def __init__(self, path: Optional[str] = "checkpoint.json"):
        self.path = path
        self.data = {"seen_ids": []}
        if path and os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {"seen_ids": []}

    def add_seen(self, ids: List[str]):
        if not ids: return
        s = set(self.data.get("seen_ids", []))
        s.update(ids)
        self.data["seen_ids"] = list(s)
        try:
            with open(self.path, "w", encoding="utf-8") as f: # type: ignore
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
