import json
import os
import uuid
from datetime import datetime


class SessionManager:
    def __init__(self, storage_dir="storage"):
        self.storage_dir = storage_dir
        self.sessions_dir = os.path.join(storage_dir, "sessions")
        self.sessions_file = os.path.join(self.sessions_dir, "sessions.json")
        os.makedirs(self.sessions_dir, exist_ok=True)
        self._ensure_file()
        self.current_id = None

    def _ensure_file(self):
        if not os.path.exists(self.sessions_file):
            with open(self.sessions_file, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2)

    def _load(self) -> list:
        with open(self.sessions_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, sessions: list):
        with open(self.sessions_file, "w", encoding="utf-8") as f:
            json.dump(sessions, f, indent=2, ensure_ascii=False)

    def start_session(self) -> str:
        sid = datetime.now().strftime("%Y%m%d-%H%M%S-") + str(uuid.uuid4())[:8]
        session = {
            "id": sid,
            "start": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "end": None
        }
        sessions = self._load()
        sessions.append(session)
        self._save(sessions)
        self.current_id = sid
        return sid

    def end_session(self):
        if not self.current_id:
            return
        sessions = self._load()
        for s in sessions:
            if s["id"] == self.current_id:
                s["end"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                break
        self._save(sessions)
        self.current_id = None

    def list_sessions(self) -> list:
        return self._load()
