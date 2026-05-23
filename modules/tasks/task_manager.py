import json
import os
from datetime import datetime

class TaskManager:
    """Basit görev yöneticisi. Görevleri JSON dosyasında saklar."""

    def __init__(self, storage_dir="storage"):
        self.storage_dir = storage_dir
        self.tasks_file = os.path.join(storage_dir, "tasks.json")
        os.makedirs(storage_dir, exist_ok=True)
        self._ensure_file()

    def _ensure_file(self):
        """JSON dosyası yoksa boş liste ile oluştur."""
        if not os.path.exists(self.tasks_file):
            with open(self.tasks_file, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _read_tasks(self):
        """Tüm görevleri listede döndür."""
        with open(self.tasks_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_tasks(self, tasks):
        """Görev listesini dosyaya yaz."""
        with open(self.tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)

    def add_task(self, description):
        """Yeni görev ekle."""
        tasks = self._read_tasks()
        task = {
            "id": len(tasks) + 1,
            "description": description,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "done": False
        }
        tasks.append(task)
        self._write_tasks(tasks)
        return task

    def list_tasks(self):
        """Tüm görevleri listele, metin olarak döndür."""
        tasks = self._read_tasks()
        if not tasks:
            return "Henüz hiç görev eklenmemiş."
        lines = []
        for t in tasks:
            durum = "✓" if t["done"] else "☐"
            lines.append(f"{durum} [{t['id']}] {t['description']} ({t['created_at']})")
        return "\n".join(lines)

    def delete_task(self, task_id):
        """Belirtilen ID'li görevi sil."""
        tasks = self._read_tasks()
        try:
            task_id = int(task_id)
        except ValueError:
            return "Geçersiz görev numarası."
        for t in tasks:
            if t["id"] == task_id:
                tasks.remove(t)
                self._write_tasks(tasks)
                return f"Görev #{task_id} silindi."
        return f"Görev #{task_id} bulunamadı."

    def mark_done(self, task_id):
        """Görevi tamamlandı olarak işaretle."""
        tasks = self._read_tasks()
        try:
            task_id = int(task_id)
        except ValueError:
            return "Geçersiz görev numarası."
        for t in tasks:
            if t["id"] == task_id:
                t["done"] = True
                self._write_tasks(tasks)
                return f"Görev #{task_id} tamamlandı olarak işaretlendi."
        return f"Görev #{task_id} bulunamadı."
