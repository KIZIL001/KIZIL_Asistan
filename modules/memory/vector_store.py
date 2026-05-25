"""JSON tabanlı vektör deposu – thread-safe, atomik yazma, sınırlı kapasite, vektörize arama."""
import os
import json
import tempfile
import threading
import time
import numpy as np
from typing import Optional

MAX_VECTORS = 10_000
DELTA_MERGE_THRESHOLD = 100


class VectorStore:
    """Konuşmaları vektör olarak saklar, kosinüs benzerliğiyle arar."""

    def __init__(self, storage_dir: str) -> None:
        self.file = os.path.join(storage_dir, "vectors.json")
        self.delta_file = os.path.join(storage_dir, "vectors_delta.json")
        self._lock = threading.RLock()
        self._data: list[dict] = []
        self._load()

    def _load(self) -> None:
        with self._lock:
            if os.path.exists(self.file):
                try:
                    with open(self.file, "r", encoding="utf-8") as f:
                        self._data = json.load(f)
                    # Geriye dönük uyumluluk: timestamp yoksa şimdiki zamanı ata
                    now = time.time()
                    for item in self._data:
                        if "timestamp" not in item:
                            item["timestamp"] = now
                except (json.JSONDecodeError, IOError):
                    self._data = []

    def _save(self) -> None:
        # Budama
        if len(self._data) > MAX_VECTORS:
            self._data = self._data[-MAX_VECTORS:]
        # Ana dosyayı atomik yaz
        tmp_fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(self.file) or ".")
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self.file)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise
        # Merge başarılı: delta dosyasını her zaman temizle
        # (tüm geçerli veri zaten ana dosyada, bozuk satırlar kurtarılamaz)
        if os.path.exists(self.delta_file):
            try:
                os.unlink(self.delta_file)
            except OSError:
                pass  # silinemezse kalır, bir sonraki merge'de tekrar dene

    def add(self, text: str, vector: list[float]) -> None:
        """Yeni metin-vektör çifti ekler. Delta dosyasına incremental append yapar."""
        entry = {"text": text, "vector": vector, "timestamp": time.time()}
        self._data.append(entry)
        # Delta dosyasına append (incremental write) – H2-4: JSON doğrulamalı
        entry_json = json.dumps(entry, ensure_ascii=False)
        try:
            # Geçerli JSON olduğunu teyit et
            json.loads(entry_json)
            with open(self.delta_file, "a", encoding="utf-8") as f:
                f.write(entry_json + "\n")
        except (IOError, json.JSONDecodeError):
            self._save()
            return
        # Delta eşiği aşıldıysa merge yap
        if os.path.exists(self.delta_file):
            try:
                with open(self.delta_file, "r", encoding="utf-8") as f:
                    delta_count = sum(1 for _ in f)
                if delta_count >= DELTA_MERGE_THRESHOLD:
                    self._save()
            except IOError:
                self._save()

    def search(self, query_vector: list[float], top_k: int = 3,
               time_decay: float = 0.0) -> list[tuple[str, float]]:
        """Kosinüs benzerliği + zaman ağırlığı ile en benzer metinleri döner.
        time_decay > 0 ise daha yeni kayıtlar avantajlıdır (0.01-0.1 önerilir).
        Dönüş: [(metin, skor), ...] — thread-safe, vektörize."""
        with self._lock:
            if not self._data:
                return []
            vectors = np.array([item["vector"] for item in self._data])
            q = np.array(query_vector)
            # Kosinüs benzerliği
            dot = np.dot(vectors, q)
            norms = np.linalg.norm(vectors, axis=1) * np.linalg.norm(q) + 1e-9
            cos_scores = dot / norms

            # Zaman ağırlığı: daha yeni = daha yüksek çarpan
            if time_decay > 0:
                now = time.time()
                timestamps = np.array([
                    item.get("timestamp", now) for item in self._data
                ])
                # Yaş (saniye), maksimum 1 gün ile normalize
                ages = np.minimum((now - timestamps) / 86400.0, 1.0)
                time_mult = 1.0 + time_decay * (1.0 - ages)
                scores = cos_scores * time_mult
            else:
                scores = cos_scores

            # En yüksek skorlu indeksleri al
            top_indices = np.argsort(scores)[::-1][:top_k]
            return [
                (self._data[i]["text"], float(scores[i]))
                for i in top_indices if scores[i] > 0
            ]

    def get_all_texts(self) -> list[str]:
        """Tüm kayıtlı metinleri döner (thread-safe)."""
        with self._lock:
            return [item["text"] for item in self._data]
