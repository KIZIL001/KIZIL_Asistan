import json
import os
import uuid


class TaskManager:
    def __init__(self, storage_dir: str):
        self.storage_dir = storage_dir
        self.file_path = os.path.join(storage_dir, "tasks.json")
        self._ensure_file()

    def _ensure_file(self):
        os.makedirs(self.storage_dir, exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2)

    def _load(self) -> list:
        with open(self.file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, tasks: list):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)

    def add_task(self, desc: str) -> dict:
        tasks = self._load()
        task = {
            "id": str(uuid.uuid4())[:8],
            "desc": desc,
            "done": False
        }
        tasks.append(task)
        self._save(tasks)
        return task

    def list_tasks(self) -> list:
        return self._load()

    def delete_task(self, task_id: str) -> bool:
        tasks = self._load()
        filtered = [t for t in tasks if t["id"] != task_id]
        if len(filtered) == len(tasks):
            return False
        self._save(filtered)
        return True

    def mark_done(self, task_id: str) -> bool:
        tasks = self._load()
        for t in tasks:
            if t["id"] == task_id:
                t["done"] = True
                self._save(tasks)
                return True
        return False
