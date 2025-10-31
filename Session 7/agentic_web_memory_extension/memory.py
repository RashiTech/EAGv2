import json
import os
from typing import Dict, List, Optional


class MemoryStore:
    """Persistent JSON-backed store for user preferences and page summaries."""

    def __init__(self, data_dir: str) -> None:
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.memory_path = os.path.join(self.data_dir, "user_memory.json")
        if not os.path.exists(self.memory_path):
            self._save({"preferences": {}, "pages": []})

    def _load(self) -> Dict:
        with open(self.memory_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data: Dict) -> None:
        with open(self.memory_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def upsert_preference(self, key: str, value) -> None:
        data = self._load()
        data.setdefault("preferences", {})[key] = value
        self._save(data)

    def get_preference(self, key: str, default=None):
        data = self._load()
        return data.get("preferences", {}).get(key, default)

    def add_page(self, url: str, summary: str) -> None:
        data = self._load()
        pages: List[Dict[str, str]] = data.setdefault("pages", [])
        pages = [p for p in pages if p.get("url") != url]
        pages.append({"url": url, "summary": summary})
        data["pages"] = pages
        self._save(data)

    def get_page_summary(self, url: str) -> Optional[str]:
        data = self._load()
        for p in data.get("pages", []):
            if p.get("url") == url:
                return p.get("summary")
        return None


