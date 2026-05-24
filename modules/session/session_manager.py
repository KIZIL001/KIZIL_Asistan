"""Oturum yönetimi – thread-safe, atomik yazma, JSON toleranslı."""
import json
import os
import uuid
import tempfile
import threading
from datetime import datetime


class SessionManager:
    def __init__(self, storage_dir: str):
        self.storage_dir = storage_dir
        self.file_path = os.path.join(storage_dir, "sessions", "sessions.json")
        self._lock = threading.RLock()
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

    def _load(self) -> list:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError, FileNotFoundError):
            return []

    def _save(self, sessions: list) -> None:
        tmp_fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(self.file_path))
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                json.dump(sessions, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, self.file_path)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    def start_session(self) -> str:
        with self._lock:
            sessions = self._load()
            session = {
                "id": str(uuid.uuid4())[:8],
                "start": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "end": None,
            }
            sessions.append(session)
            self._save(sessions)
            return session["id"]

    def end_session(self, session_id: str | None = None) -> None:
        with self._lock:
            sessions = self._load()
            if session_id:
                for s in sessions:
                    if s.get("id") == session_id and s.get("end") is None:
                        s["end"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        self._save(sessions)
                        return
                # ID verildi ama bulunamadı → alt bloğa düşme
                return

            # ID verilmezse son açık oturumu kapat
            for s in reversed(sessions):
                if s.get("end") is None:
                    s["end"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self._save(sessions)
                    return

    def list_sessions(self) -> list:
        with self._lock:
            return self._load()
