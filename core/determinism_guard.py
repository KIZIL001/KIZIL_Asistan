"""KIZIL Determinism Guard - Dinamik config, LRU cache, kanonik hash."""
import hashlib, json
from collections import OrderedDict
from pathlib import Path
from datetime import datetime

class DeterminismGuard:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_ready'):
            self._ready = True
            self._hash_store = OrderedDict()
            self._max_entries = 1000
            self._log_dir = Path("storage/diagnostics")
            self._log_dir.mkdir(parents=True, exist_ok=True)

    def _is_enabled(self):
        from utils.config import Config
        return Config()._data.get("ENABLE_DETERMINISM_GUARD", False)

    def _canonical(self, obj):
        if isinstance(obj, dict):
            return tuple(sorted((k, self._canonical(v)) for k, v in obj.items()))
        elif isinstance(obj, list):
            return tuple(self._canonical(item) for item in obj)
        else:
            return obj

    def _input_hash(self, messages: list, model: str) -> str:
        canonical = self._canonical(messages)
        raw = str(canonical) + model
        return hashlib.sha256(raw.encode()).hexdigest()

    def check(self, messages: list, model: str, response: str) -> bool:
        if not self._is_enabled():
            return True
        inp_hash = self._input_hash(messages, model)
        resp_hash = hashlib.sha256(response.encode()).hexdigest()
        if inp_hash in self._hash_store:
            if self._hash_store[inp_hash] != resp_hash:
                self._log_divergence(inp_hash, self._hash_store[inp_hash], resp_hash)
                return False
            self._hash_store.move_to_end(inp_hash)  # LRU: hit alanı sona taşı
        else:
            self._hash_store[inp_hash] = resp_hash
            if len(self._hash_store) > self._max_entries:
                self._hash_store.popitem(last=False)  # En eskiyi sil
        return True

    def _log_divergence(self, inp_hash: str, old_hash: str, new_hash: str):
        alert = {
            "timestamp": datetime.now().isoformat(),
            "type": "DETERMINISM_DIVERGENCE",
            "input_hash": inp_hash,
            "previous_response_hash": old_hash,
            "current_response_hash": new_hash
        }
        fname = f"diverge_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        (self._log_dir / fname).write_text(json.dumps(alert, indent=2, ensure_ascii=False))
