"""KIZIL Tool Reliability Layer - Bellek ici, dinamik config, deterministik."""
import json
from pathlib import Path

class ToolReliability:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_ready'):
            self._ready = True
            self._storage = Path("storage/tool_reliability.json")
            self._counters = {}
        self._load()

    def _is_enabled(self):
        from utils.config import Config
        return Config()._data.get("ENABLE_TOOL_RELIABILITY", False)

    def _load(self):
        if self._storage.exists():
            try:
                self._counters = json.loads(self._storage.read_text())
            except:
                self._counters = {}

    def save(self):
        if not self._is_enabled():
            return
        self._storage.parent.mkdir(parents=True, exist_ok=True)
        self._storage.write_text(json.dumps(self._counters, indent=2, ensure_ascii=False))

    def increment_call(self, tool_name: str):
        if not self._is_enabled():
            return
        if tool_name not in self._counters:
            self._counters[tool_name] = {"calls": 0, "failures": 0}
        self._counters[tool_name]["calls"] += 1

    def increment_failure(self, tool_name: str):
        if not self._is_enabled():
            return
        if tool_name not in self._counters:
            self._counters[tool_name] = {"calls": 0, "failures": 0}
        self._counters[tool_name]["failures"] += 1

    def get_reliability(self, tool_name: str) -> float:
        if tool_name in self._counters:
            c = self._counters[tool_name]
            total = c["calls"]
            return 100.0 if total == 0 else round((1 - c["failures"] / total) * 100, 1)
        return 100.0

    def get_all(self) -> dict:
        return {n: self.get_reliability(n) for n in self._counters}
