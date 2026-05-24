"""JSON tabanlı vektör deposu – thread-safe, kapsüllü."""
import os
import json
import threading
import numpy as np
from typing import Optional


class VectorStore:
    """Konuşmaları vektör olarak saklar, kosinüs benzerliğiyle arar."""

    def __init__(self, storage_dir: str) -> None:
        self.file = os.path.join(storage_dir, "vectors.json")
        self._lock = threading.RLock()
        self._data: list[dict] = []
        self._load()

    def _load(self) -> None:
        with self._lock:
            if os.path.exists(self.file):
                try:
                    with open(self.file, "r", encoding="utf-8") as f:
                        self._data = json.load(f)
                except (json.JSONDecodeError, IOError):
                    self._data = []

    def _save(self) -> None:
        with self._lock:
            with open(self.file, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)

    def add(self, text: str, vector: list[float]) -> None:
        """Yeni metin-vektör çifti ekler (thread-safe)."""
        with self._lock:
            self._data.append({"text": text, "vector": vector})
            self._save()

    def search(self, query_vector: list[float], top_k: int = 3) -> list[str]:
        """Kosinüs benzerliğiyle en benzer metinleri döner (thread-safe)."""
        with self._lock:
            if not self._data:
                return []
            q = np.array(query_vector)
            scores = []
            for item in self._data:
                v = np.array(item["vector"])
                cos = np.dot(q, v) / (np.linalg.norm(q) * np.linalg.norm(v) + 1e-9)
                scores.append((cos, item["text"]))
            scores.sort(key=lambda x: x[0], reverse=True)
            return [text for _, text in scores[:top_k]]

    def get_all_texts(self) -> list[str]:
        """Tüm kayıtlı metinleri döner (thread-safe)."""
        with self._lock:
            return [item["text"] for item in self._data]
