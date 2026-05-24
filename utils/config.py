import json
import os
import tempfile
import threading


class Config:
    _instance = None
    _init_lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._lock = threading.RLock()
                    cls._instance._load()
        return cls._instance

    def _load(self):
        config_file = os.path.join("storage", "config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._data = self._defaults()
        else:
            self._data = self._defaults()

    def _defaults(self):
        return {
            "STORAGE_DIR": "storage",
            "CONVERSATIONS_DIR": "conversations",
            "MEMORY_DIR": "memory",
            "LOG_FILE": "kizil.log",
            "LOG_LEVEL": "DEBUG",
            "LLM_MODEL": "phi3:mini",
            "SUMMARY_MAX_LINES": 50,
            "DEFAULT_UNKNOWN_RESPONSE": "Henüz tam olarak anlayamadım. Biraz daha basit sormayı dene ya da 'yardım' yaz."
        }

    def __getattr__(self, name):
        with self._lock:
            if name in self._data:
                return self._data[name]
            raise AttributeError(f"Config'de '{name}' bulunamadı")

    def set(self, key: str, value):
        with self._lock:
            self._data[key] = value
            self._save()

    def _save(self):
        """Atomik yazma: önce geçici dosyaya, sonra replace."""
        config_file = os.path.join("storage", "config.json")
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        tmp_fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(config_file))
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, config_file)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    def save(self):
        """Dışarıdan çağrılabilecek kaydetme (thread-safe)."""
        with self._lock:
            self._save()
