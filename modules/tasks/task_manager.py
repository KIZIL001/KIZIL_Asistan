import json
import os
import uuid
import tempfile
from datetime import datetime, timezone
from datetime import datetime, timezone


class TaskManager:
    def __init__(self, storage_dir: str):
        self.storage_dir = storage_dir
        self.file_path = os.path.join(storage_dir, "tasks.json")

    def _load(self) -> list:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                tasks = json.load(f)
                # Eski görevleri yeni state makinesine migrate et
                for task in tasks:
                    if "status" not in task:
                        task["status"] = "done" if task.get("done") else "pending"
                    if "retry_count" not in task:
                        task["retry_count"] = 0
                    if "max_retry" not in task:
                        task["max_retry"] = 3
                    if "created_at" not in task:
                        task["created_at"] = datetime.now(timezone.utc).isoformat()
                    if "last_error" not in task:
                        task["last_error"] = None
                    if "input" not in task:
                        task["input"] = {}
                    # done alanını status ile senkronize tut
                    task["done"] = (task["status"] == "done")
                return tasks
        except (json.JSONDecodeError, IOError, FileNotFoundError):
            return []

    def _save(self, tasks: list):
        os.makedirs(self.storage_dir, exist_ok=True)
        tmp_fd, tmp_path = None, None
        try:
            tmp_fd, tmp_path = tempfile.mkstemp(dir=self.storage_dir)
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                json.dump(tasks, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, self.file_path)
        except Exception:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    def add_task(self, desc: str, max_retry: int = 3, input_data: dict = None) -> dict:
        tasks = self._load()
        for _ in range(10):
            new_id = str(uuid.uuid4())[:8]
            if not any(t["id"] == new_id for t in tasks):
                break
        task = {
            "id": new_id,
            "desc": desc,
            "done": False,
            "depends_on": None,
            "status": "pending",
            "retry_count": 0,
            "max_retry": max_retry,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_error": None,
            "input": input_data if input_data is not None else {},
        }
        tasks.append(task)
        self._save(tasks)
        return task

    def add_raw_task(self, task: dict) -> None:
        # Eksik alanları tamamla
        defaults = {
            "done": False,
            "status": "pending",
            "retry_count": 0,
            "max_retry": 3,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_error": None,
            "input": {},
        }
        for key, default in defaults.items():
            if key not in task:
                task[key] = default
        tasks = self._load()
        tasks.append(task)
        self._save(tasks)

    def list_tasks(self) -> list:
        return self._load()

    def delete_task(self, task_id: str) -> bool:
        tasks = self._load()
        for t in tasks:
            if t.get("depends_on") == task_id:
                t["depends_on"] = None
        filtered = [t for t in tasks if t["id"] != task_id]
        if len(filtered) == len(tasks):
            return False
        self._save(filtered)
        return True

    # Geriye dönük uyumluluk
    def mark_done(self, task_id: str) -> tuple[bool, str]:
        return self.complete_task(task_id)

    def complete_task(self, task_id: str) -> tuple[bool, str]:
        can_do, reason = self.can_complete(task_id)
        if not can_do:
            return False, reason
        tasks = self._load()
        for t in tasks:
            if t["id"] == task_id:
                t["status"] = "done"
                t["done"] = True
                t["last_error"] = None
                self._save(tasks)
                return True, f"Görev #{task_id} tamamlandı."
        return False, f"Görev #{task_id} bulunamadı."

    def start_task(self, task_id: str) -> tuple[bool, str]:
        tasks = self._load()
        task = None
        for t in tasks:
            if t["id"] == task_id:
                task = t
                break
        if not task:
            return False, f"Görev #{task_id} bulunamadı."
        if task["status"] != "pending":
            return False, f"Görev #{task_id} şu anda '{task['status']}' durumunda, başlatılamaz."
        can_do, reason = self.can_complete(task_id)
        if not can_do:
            return False, reason
        task["status"] = "running"
        task["done"] = False
        task["last_error"] = None
        self._save(tasks)
        return True, f"Görev #{task_id} başlatıldı."

    def fail_task(self, task_id: str, error: str) -> tuple[bool, str]:
        tasks = self._load()
        task = None
        for t in tasks:
            if t["id"] == task_id:
                task = t
                break
        if not task:
            return False, f"Görev #{task_id} bulunamadı."
        if task["status"] not in ("running", "pending"):
            return False, f"Görev #{task_id} '{task['status']}' durumunda, başarısız işaretlenemez."
        task["status"] = "failed"
        task["last_error"] = error
        task["retry_count"] += 1
        task["done"] = False
        self._save(tasks)
        return True, f"Görev #{task_id} başarısız. Hata: {error}"

    def retry_task(self, task_id: str) -> tuple[bool, str]:
        tasks = self._load()
        task = None
        for t in tasks:
            if t["id"] == task_id:
                task = t
                break
        if not task:
            return False, f"Görev #{task_id} bulunamadı."
        if task["status"] != "failed":
            return False, f"Görev #{task_id} yalnızca 'failed' durumunda tekrar denenebilir, şu an '{task['status']}'."
        if task["retry_count"] >= task["max_retry"]:
            return False, f"Görev #{task_id} maksimum deneme sayısına ulaştı ({task['max_retry']})."
        task["status"] = "pending"
        task["last_error"] = None
        task["done"] = False
        self._save(tasks)
        return True, f"Görev #{task_id} yeniden denemeye alındı. Kalan hak: {task['max_retry'] - task['retry_count']}"

    def unmark_done(self, task_id: str) -> bool:
        tasks = self._load()
        for t in tasks:
            if t["id"] == task_id:
                t["done"] = False
                t["status"] = "pending"
                self._save(tasks)
                return True
        return False

    def chain_tasks(self, first_id: str, second_id: str) -> str:
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
            "status": task["status"],
            "depends_on": task.get("depends_on"),
            "blocked": False,
            "blocked_by": None,
            "retry_count": task["retry_count"],
            "max_retry": task["max_retry"],
            "created_at": task["created_at"],
            "last_error": task["last_error"],
            "input": task["input"],
        }
        if task.get("depends_on"):
            for t in tasks:
                if t["id"] == task["depends_on"] and t["status"] != "done":
                    info["blocked"] = True
                    info["blocked_by"] = t["id"]
                    break
        return info

    def can_complete(self, task_id: str) -> tuple[bool, str]:
        info = self.get_chain_info(task_id)
        if not info:
            return False, "Görev bulunamadı."
        if info.get("blocked"):
            return False, f"Bu görev #{info['blocked_by']} görevine bağlı. Önce onu tamamlamalısın."
        return True, ""
