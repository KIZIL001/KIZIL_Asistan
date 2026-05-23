import json
import os

class Config:
    _instance = None
    _data = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self):
        config_file = os.path.join("storage", "config.json")
        if os.path.exists(config_file):
            with open(config_file, "r", encoding="utf-8") as f:
                self._data = json.load(f)
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
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"Config'de '{name}' bulunamadı")

    def save(self):
        config_file = os.path.join("storage", "config.json")
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)
