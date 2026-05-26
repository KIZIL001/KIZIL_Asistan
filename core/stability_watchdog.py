"""
Stability Watchdog – Pasif kararlılık gözlemcisi.
Hiçbir arka plan işlemi, timer veya thread içermez.
Yalnızca hook'larla (start, stop, heartbeat) beslenir.
"""
import os
import time
import json
from datetime import datetime, timezone
from utils.file_utils import atomic_write_json, atomic_read_json

WATCHDOG_FILE = "storage/stability_watchdog.json"
CLEAN_EXIT_KEY = "clean_exit"


class StabilityWatchdog:
    def __init__(self):
        self.data = atomic_read_json(WATCHDOG_FILE, {
            "total_sessions": 0,
            "total_crashes": 0,
            "total_uptime_seconds": 0,
            "last_heartbeat": None,
            CLEAN_EXIT_KEY: True,
            "session_history": []
        })
        self._session_start: float | None = None
        self._last_heartbeat: float | None = None

    def on_start(self):
        """Oturum başlangıç hook'u. Önceki crash'i tespit et."""
        if not self.data.get(CLEAN_EXIT_KEY, True):
            self.data["total_crashes"] += 1
            self._save()
        self.data[CLEAN_EXIT_KEY] = False
        self._session_start = time.time()
        self._last_heartbeat = self._session_start
        self._save()

    def heartbeat(self):
        """Her turda çağrılır. RAM'deki zamanı günceller, diske yazmaz."""
        self._last_heartbeat = time.time()

    def on_stop(self):
        """Düzgün kapanış hook'u."""
        if self._session_start:
            uptime = int(time.time() - self._session_start)
            self.data["total_uptime_seconds"] += uptime
            self.data["total_sessions"] += 1
            self.data["session_history"].append({
                "start": datetime.fromtimestamp(self._session_start, tz=timezone.utc).isoformat(),
                "uptime_seconds": uptime,
                "clean_exit": True
            })
            # Geçmişi sınırla (son 50 oturum)
            if len(self.data["session_history"]) > 50:
                self.data["session_history"] = self.data["session_history"][-50:]
        self.data[CLEAN_EXIT_KEY] = True
        self._save()

    def _save(self):
        """Atomik yazma ile diske kaydet."""
        atomic_write_json(WATCHDOG_FILE, self.data)

    def get_report(self) -> dict:
        """Mevcut metriklerin bir kopyasını döndürür."""
        return dict(self.data)
