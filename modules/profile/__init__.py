"""Kullanıcı profili yönetimi – thread-safe, atomik yazma, toplu güncelleme."""
import os
import json
import tempfile
import threading
from utils.config import Config


class ProfileManager:
    def __init__(self):
        self.config = Config()
        self.file = os.path.join(self.config.STORAGE_DIR, "profile.json")
        self._lock = threading.RLock()
        # Dizin varlığını garanti altına al
        os.makedirs(os.path.dirname(self.file) or ".", exist_ok=True)
        self._data = self._load()

    def _defaults(self) -> dict:
        return {
            "ad": "",
            "tercihler": {},
            "notlar": "",
            "model": self.config.LLM_MODEL,
        }

    def _load(self) -> dict:
        with self._lock:
            if os.path.exists(self.file):
                try:
                    with open(self.file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    defaults = self._defaults()
                    for k, v in defaults.items():
                        if k not in data:
                            data[k] = v
                    return data
                except (json.JSONDecodeError, IOError):
                    pass
            return self._defaults()

    def save(self) -> None:
        with self._lock:
            tmp_fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(self.file) or ".")
            try:
                with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                    json.dump(self._data, f, ensure_ascii=False, indent=2)
                os.replace(tmp_path, self.file)
            except Exception:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                raise

    def get(self, key: str, default=None):
        with self._lock:
            return self._data.get(key, default)

    def set(self, key: str, value, auto_save: bool = True) -> None:
        with self._lock:
            self._data[key] = value
            if auto_save:
                self.save()

    def update_batch(self, updates: dict) -> None:
        with self._lock:
            for key, value in updates.items():
                self._data[key] = value
            self.save()

    def get_all(self) -> dict:
        with self._lock:
            return dict(self._data)

    def get_prompt(self) -> str:
        return ""

    def update_from_summary(self, summary: str) -> None:
        with self._lock:
            if self._data.get("notlar"):
                self._data["notlar"] += "\n" + summary
            else:
                self._data["notlar"] = summary
            self.save()
