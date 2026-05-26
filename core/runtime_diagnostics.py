"""KIZIL Runtime Diagnostics - State'i koruyan, config duyarli Singleton."""
import json, time, tracemalloc
from pathlib import Path
from datetime import datetime

class RuntimeDiagnostics:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        from utils.config import Config
        self._enabled = Config()._data.get("ENABLE_RUNTIME_DIAGNOSTICS", False)

        # Ilk kez kurulum (state yarat)
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._storage_ready = True
            self._storage_ready = True
            self.storage_dir = Path("storage/diagnostics")
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            self.counters = {
                "llm_calls": 0,
                "llm_retries": 0,
                "llm_errors": 0,
                "tool_failures": 0,
                "context_prunes": 0,
                "poisoning_detections": 0,
            }
            self.start_time = time.time()
            self.turn_count = 0
            self.snapshot_interval = 10
            self._tracemalloc_started = False

        # tracemalloc sadece bir kez başlat
        if self._enabled and not self._tracemalloc_started:
            tracemalloc.start()
            self._tracemalloc_started = True

    def increment(self, key: str, delta: int = 1):
        if not self._enabled:
            return
        if key in self.counters:
            self.counters[key] += delta

    def snapshot(self) -> dict:
        if not self._enabled:
            return {}
        uptime = time.time() - self.start_time
        current, peak = tracemalloc.get_traced_memory() if self._tracemalloc_started else (0, 0)
        return {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": round(uptime, 1),
            "turn_count": self.turn_count,
            "memory_current_kb": round(current / 1024, 1),
            "memory_peak_kb": round(peak / 1024, 1),
            **self.counters
        }

    def save(self):
        if not self._enabled:
            return ""
        snap = self.snapshot()
        fname = f"diag_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
        path = self.storage_dir / fname
        path.write_text(json.dumps(snap, indent=2, ensure_ascii=False))
        return str(path)
