import json
import os
import uuid
import threading


class TaskManager:
    def __init__(self, storage_dir: str):
        self.storage_dir = storage_dir
        self.file_path = os.path.join(storage_dir, "tasks.json")
        self._lock = threading.RLock()  # Reentrant: can_complete → get_chain_info zincirinde deadlock engellenir

    def _load(self) -> list:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError, FileNotFoundError):
            return []

    def _save(self, tasks: list):
        os.makedirs(self.storage_dir, exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)

    def add_task(self, desc: str) -> dict:
        with self._lock:
            tasks = self._load()
            for _ in range(10):
                new_id = str(uuid.uuid4())[:8]
                if not any(t["id"] == new_id for t in tasks):
                    break
            task = {
                "id": new_id,
                "desc": desc,
                "done": False,
                "depends_on": None
            }
            tasks.append(task)
            self._save(tasks)
            return task

    def add_raw_task(self, task: dict) -> None:
        with self._lock:
            tasks = self._load()
            tasks.append(task)
            self._save(tasks)

    def list_tasks(self) -> list:
        with self._lock:
            return self._load()

    def delete_task(self, task_id: str) -> bool:
        with self._lock:
            tasks = self._load()
            for t in tasks:
                if t.get("depends_on") == task_id:
                    t["depends_on"] = None
            filtered = [t for t in tasks if t["id"] != task_id]
            if len(filtered) == len(tasks):
                return False
            self._save(filtered)
            return True

    def mark_done(self, task_id: str) -> tuple[bool, str]:
        with self._lock:
            can_do, reason = self.can_complete(task_id)
            if not can_do:
                return False, reason
            tasks = self._load()
            for t in tasks:
                if t["id"] == task_id:
                    t["done"] = True
                    self._save(tasks)
                    return True, f"Görev #{task_id} tamamlandı."
            return False, f"Görev #{task_id} bulunamadı."

    def unmark_done(self, task_id: str) -> bool:
        with self._lock:
            tasks = self._load()
            for t in tasks:
                if t["id"] == task_id:
                    t["done"] = False
                    self._save(tasks)
                    return True
            return False

    def chain_tasks(self, first_id: str, second_id: str) -> str:
        with self._lock:
            tasks = self._load()
            first = None
            second = None
            for t in tasks:
                if t["id"] == first_id:
                    first = t
                if t["id"] == second_id:
                    second = t
            if not first:
                return f"Görev #{first_id} bulunamadı."
            if not second:
                return f"Görev #{second_id} bulunamadı."
            if first_id == second_id:
                return "Bir görev kendisine bağlanamaz."
            if first.get("depends_on") == second_id:
                return "Bu zincir ters yönlü bir döngü oluşturur, izin verilmez."
            visited = set()
            current = self._get_depends_on(tasks, first_id)
            max_depth = 100
            while current and max_depth > 0:
                if current == second_id:
                    return "Bu zincir döngü oluşturur, izin verilmez."
                if current in visited:
                    break
                visited.add(current)
                current = self._get_depends_on(tasks, current)
                max_depth -= 1
            second["depends_on"] = first_id
            self._save(tasks)
            return f"Görev #{second_id}, #{first_id} görevine bağlandı."

    def _get_depends_on(self, tasks: list, task_id: str) -> str | None:
        for t in tasks:
            if t["id"] == task_id:
                return t.get("depends_on")
        return None

    def get_chain_info(self, task_id: str) -> dict:
        with self._lock:
            tasks = self._load()
            task = None
            for t in tasks:
                if t["id"] == task_id:
                    task = t
                    break
            if not task:
                return {}
            info = {
                "id": task["id"],
                "desc": task["desc"],
                "done": task["done"],
                "depends_on": task.get("depends_on"),
                "blocked": False,
                "blocked_by": None,
            }
            if task.get("depends_on"):
                for t in tasks:
                    if t["id"] == task["depends_on"] and not t.get("done"):
                        info["blocked"] = True
                        info["blocked_by"] = t["id"]
                        break
            return info

    def can_complete(self, task_id: str) -> tuple[bool, str]:
        with self._lock:
            info = self.get_chain_info(task_id)
            if not info:
                return False, "Görev bulunamadı."
            if info.get("blocked"):
                return False, f"Bu görev #{info['blocked_by']} görevine bağlı. Önce onu tamamlamalısın."
            return True, ""
