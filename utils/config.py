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
        if "_last_hash" not in self._data:
            self._data["_last_hash"] = self._compute_hash()

    def _defaults(self):
        return {
            "ENABLE_UNCERTAINTY_FILTER": True,
            "STORAGE_DIR": "storage",
            "CONVERSATIONS_DIR": "conversations",
            "MEMORY_DIR": "memory",
            "LOG_FILE": "kizil.log",
            "LOG_LEVEL": "DEBUG",
            "LLM_MODEL": "phi3:mini",
            "SUMMARY_MAX_LINES": 50,
            "DEFAULT_UNKNOWN_RESPONSE": "Hen\u00fcz tam olarak anlayamad\u0131m. Biraz daha basit sormay\u0131 dene ya da 'yard\u0131m' yaz.",
            "ENABLE_DECISION_TRACE": True,
            "ENABLE_JACCARD_PRUNING": True,
            "ENABLE_RESPONSE_TEMPLATES": True,
            "ENABLE_TOOL_VERIFICATION": True,
            "ENABLE_PROMPT_FIREWALL": True,
            "ENABLE_CONTEXT_POISONING_DEFENSE": True,
            "ENABLE_GOLDEN_SESSION_RECORDING": False,
            "ENABLE_FAILURE_CORPUS": True,
            "ENABLE_RUNTIME_DIAGNOSTICS": False,
            "ENABLE_DETERMINISM_GUARD": False,
            "ENABLE_TOOL_RELIABILITY": False,
            "ENABLE_PROMPT_DISCIPLINE": False,
        }

    def __getattr__(self, name):
        with self._lock:
            if name in self._data:
                return self._data[name]
            raise AttributeError(f"Config'de '{name}' bulunamad\u0131")

    def set(self, key: str, value):
        with self._lock:
            if self._data.get("_frozen", False):
                raise PermissionError(f"Config dondurulmuş. '{key}' değiştirilemez.")
            self._data[key] = value
            self._save()
            self._save_backup("auto")

    def _save(self):
        """Atomik yazma: \u00f6nce ge\u00e7ici dosyaya, sonra replace."""
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
        """D\u0131\u015far\u0131dan \u00e7a\u011fr\u0131labilecek kaydetme (thread-safe)."""
        with self._lock:
            self._save()

    # ========================================================================
    # CONFIG IMMUTABILITY & ROLLBACK (Faz 3)
    # ========================================================================

    def freeze(self) -> None:
        """Config'i dondur. Bundan sonra set() çağrıları reddedilir."""
        with self._lock:
            self._data["_frozen"] = True
            self._save()
        self._save_backup("frozen")

    def unfreeze(self) -> None:
        """Config dondurmayı kaldır."""
        with self._lock:
            self._data["_frozen"] = False
            self._save()

    def is_frozen(self) -> bool:
        return self._data.get("_frozen", False)

    def _compute_hash(self) -> str:
        """Config verisinin deterministik hash'i (meta anahtarlar hariç)."""
        import hashlib
        import json
        data_to_hash = {k: v for k, v in self._data.items() if not k.startswith("_")}
        serialized = json.dumps(data_to_hash, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]

    def detect_drift(self) -> bool:
        """Binary drift tespiti. True = sapma var."""
        with self._lock:
            current = self._compute_hash()
            saved = self._data.get("_last_hash", "")
            return current != saved

    def _save_backup(self, tag: str = "manual") -> None:
        """Maksimum 5 yedek al, eskileri sil."""
        import os
        import json
        backup_dir = os.path.join(self.STORAGE_DIR, "config_backups")
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"config_{tag}_{timestamp}.json")
        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)
        backups = sorted([f for f in os.listdir(backup_dir) if f.startswith("config_")])
        while len(backups) > 5:
            oldest = backups.pop(0)
            os.remove(os.path.join(backup_dir, oldest))

    def rollback(self, backup_index: int = -1) -> bool:
        """Belirtilen yedeğe dön. Varsayılan: en son yedek."""
        import os
        import json
        backup_dir = os.path.join(self.STORAGE_DIR, "config_backups")
        if not os.path.exists(backup_dir):
            return False
        backups = sorted([f for f in os.listdir(backup_dir) if f.startswith("config_")])
        if not backups:
            return False
        try:
            target = backups[backup_index]
            target_path = os.path.join(backup_dir, target)
            with open(target_path, "r", encoding="utf-8") as f:
                backup_data = json.load(f)
            with self._lock:
                self._data = backup_data
                self._data["_frozen"] = False
                self._data["_last_hash"] = self._compute_hash()
                self._save()
            return True
        except (IndexError, FileNotFoundError, json.JSONDecodeError):
            return False

    def list_backups(self) -> list:
        """Mevcut yedeklerin listesi."""
        import os
        backup_dir = os.path.join(self.STORAGE_DIR, "config_backups")
        if not os.path.exists(backup_dir):
            return []
        return sorted([f for f in os.listdir(backup_dir) if f.startswith("config_")])

