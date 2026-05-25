import os
from core.session_replay import SessionRecorder
from core.failure_corpus import FailureRecorder
from utils.config import Config
import time
import threading
from datetime import datetime
from collections import deque
from utils.config import Config
from modules.memory.vector_store import VectorStore

EMBED_CACHE_TTL = 300
EMBED_CACHE_MAX = 1000
OZET_SAKLAMA_GUN = 30
MAX_OZET_DOSYASI = 50
MAX_OZET_CONTEXT = 5


class MemoryManager:
    """
    KIZIL Asistan'ın hafıza yöneticisi.
    - Kısa süreli hafıza (context deque): son konuşma akışı
    - Uzun süreli hafıza (vector_store + özetler): geçmiş bilgi kalıcılığı
    """

    def __init__(self):
        self.config = Config()
        self.storage_path = self.config.STORAGE_DIR
        self.conversations_dir = os.path.join(self.storage_path, self.config.CONVERSATIONS_DIR)
        self.memory_dir = os.path.join(self.storage_path, self.config.MEMORY_DIR)
        self.conversation_file = os.path.join(self.conversations_dir, "gunluk.txt")

        os.makedirs(self.conversations_dir, exist_ok=True)
        os.makedirs(self.memory_dir, exist_ok=True)

        # Kısa süreli hafıza
        self.context = deque(maxlen=self.config.SUMMARY_MAX_LINES)

        # Uzun süreli hafıza
        self.vector_store = VectorStore(storage_dir=self.memory_dir)

        # Embedding önbelleği
        self._embed_cache: dict[int, tuple[list[float], float]] = {}

        # Thread güvenliği
        self._lock = threading.RLock()

        self.logger = None


        # Golden session recording
        if Config()._data.get("ENABLE_GOLDEN_SESSION_RECORDING", False):
            self._golden_recorder = SessionRecorder(
                session_id=f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
        else:
            self._golden_recorder = None

        # Failure corpus recording
        if Config()._data.get("ENABLE_FAILURE_CORPUS", False):
            self._failure_recorder = FailureRecorder()
        else:
            self._failure_recorder = None
    def set_logger(self, logger):
        self.logger = logger

    def _log(self, level: str, msg: str) -> None:
        if self.logger:
            getattr(self.logger, level, self.logger.info)(msg)

    # ========================================================================
    # KISA SÜRELİ HAFIZA (Short-Term Memory)
    # ========================================================================

    def add_short_term(self, role: str, message: str) -> None:
        self.context.append({"role": role, "content": message})

    def get_short_term(self) -> list:
        return list(self.context)

    def clear_short_term(self) -> None:
        self.context.clear()



    # ========================================================================
    # UZUN SÜRELİ HAFIZA (Long-Term Memory) - Embedding
    # ========================================================================

    def _get_embedding(self, text: str) -> list[float] | None:
        text_hash = hash(text)
        su_an = time.time()
        if len(self._embed_cache) > EMBED_CACHE_MAX:
            # Önce süresi dolanları temizle
            su_an = time.time()
            expired = [h for h, (v, ts) in self._embed_cache.items() if su_an - ts > EMBED_CACHE_TTL]
            for h in expired:
                del self._embed_cache[h]
            # Hâlâ sınır aşıldıysa en eski %25'i at
            if len(self._embed_cache) > EMBED_CACHE_MAX:
                sorted_items = sorted(self._embed_cache.items(), key=lambda x: x[1][1])
                remove_count = max(1, int(len(sorted_items) * 0.25))
                for h, _ in sorted_items[:remove_count]:
                    del self._embed_cache[h]
        if text_hash in self._embed_cache:
            vec, ts = self._embed_cache[text_hash]
            if su_an - ts < EMBED_CACHE_TTL:
                return vec
            del self._embed_cache[text_hash]
        try:
            import ollama  # type: ignore
            response = ollama.embeddings(model="nomic-embed-text", prompt=text)
            vec = response.get("embedding")
            if vec:
                self._embed_cache[text_hash] = (vec, su_an)
            return vec
        except Exception as e:
            self._log("error", f"Embedding alınamadı: {e}")
            if self._failure_recorder:
                self._failure_recorder.record("embedding_error", str(e), {"context": "add_long_term"})
            return None

    def add_long_term(self, text: str) -> None:
        with self._lock:
            try:
                vec = self._get_embedding(text)
                if vec:
                    self.vector_store.add(text, vec)
            except Exception as e:
                self._log("error", f"Uzun süreli hafızaya eklenemedi: {e}")

    def get_long_term(self, max_items: int = 20) -> str:
        texts = self.vector_store.get_all_texts()
        return "\n---\n".join(texts[-max_items:])

    # ========================================================================
    # HAFIZA SIRALAMA (Memory Ranking)
    # ========================================================================

    def rank_memories(self, query: str, top_k: int = 5) -> list[tuple[str, float]]:
        with self._lock:
            try:
                import numpy as np  # type: ignore
                q_vec = self._get_embedding(query)
                if not q_vec:
                    return []
                q = np.array(q_vec)
                entries = self.vector_store.get_all_entries()
                results = []
                for item in entries:
                    v = np.array(item["vector"])
                    cos = np.dot(q, v) / (np.linalg.norm(q) * np.linalg.norm(v) + 1e-9)
                    results.append((item["text"], float(cos)))
                results.sort(key=lambda x: x[1], reverse=True)
                return results[:top_k]
            except Exception as e:
                self._log("error", f"Hafıza sıralama hatası: {e}")
                if self._failure_recorder:
                    self._failure_recorder.record("memory_sort_error", str(e))
                return []

    # ========================================================================
    # KONUŞMA KAYDI VE ÖZETLEME
    # ========================================================================

    def save_conversation(self, user_input: str, response: str):
        zaman = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._lock:
            try:
                with open(self.conversation_file, "a", encoding="utf-8") as f:
                    f.write(f"{zaman} | Kullanici: {user_input}\n")
                    f.write(f"{zaman} | KIZIL: {response}\n")
                    f.write("-" * 30 + "\n")
            except Exception as e:
                self._log("error", f"Konuşma kaydedilemedi: {e}")
                if self._failure_recorder:
                    self._failure_recorder.record("conversation_save_error", str(e))

            self.add_long_term(f"Kullanici: {user_input}\nKIZIL: {response}")


            # Golden session recording
            if self._golden_recorder:
                self._golden_recorder.record_turn(user_input, response)
                self._golden_recorder.save()
    def _read_last_lines(self, max_lines: int) -> str:
        if not os.path.exists(self.conversation_file):
            return ""
        with self._lock:
            with open(self.conversation_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
        return "".join(lines[-max_lines:])

    def _clean_old_summaries(self):
        if not os.path.isdir(self.memory_dir):
            return
        ozetler = sorted([f for f in os.listdir(self.memory_dir) if f.startswith("ozet_") and f.endswith(".txt")])
        su_an = time.time()
        esik = su_an - (OZET_SAKLAMA_GUN * 86400)
        for dosya in list(ozetler):
            dosya_yolu = os.path.join(self.memory_dir, dosya)
            try:
                mtime = os.path.getmtime(dosya_yolu)
                if mtime < esik:
                    os.remove(dosya_yolu)
                    ozetler.remove(dosya)
            except OSError:
                pass
        while len(ozetler) > MAX_OZET_DOSYASI:
            eski = ozetler.pop(0)
            try:
                os.remove(os.path.join(self.memory_dir, eski))
            except OSError:
                pass

    def summarize_and_save(self, model_name, chat_module):
        recent = self._read_last_lines(self.config.SUMMARY_MAX_LINES)
        if not recent.strip():
            return None, "Henüz kayıtlı konuşma yok."

        # Önceki özetleri bağlam olarak al
        onceki_ozetler = self._load_all_summaries()
        onceki_parcalar = onceki_ozetler.split("\n\n---\n\n")
        son_ozetler = "\n---\n".join(onceki_parcalar[-MAX_OZET_CONTEXT:]) if onceki_ozetler.strip() else ""

        if son_ozetler:
            prompt = (
                "GÖREV: Aşağıdaki önceki özetleri ve son konuşma kaydını kullanarak "
                "güncel bir birleşik özet çıkar.\n"
                "KURALLAR:\n"
                "1. Önceki özetlerdeki bilgileri aynen tekrar etme, onları özetle.\n"
                "2. Sadece yeni ve değişen bilgileri ekle.\n"
                "3. Sonuç tek bir kısa paragraf olsun.\n"
                "4. Sadece özeti yaz, başka bir şey yazma.\n\n"
                "ÖNCEKİ ÖZETLER:\n" + son_ozetler + "\n\n"
                "SON KONUŞMA KAYDI:\n" + recent
            )
        else:
            prompt = (
                "Aşağıdaki konuşma kaydından önemli noktaları, alınan kararları "
                "ve kullanıcı hakkında edinilen bilgileri kısa bir özet halinde çıkar. "
                "Sadece özeti yaz, başka bir şey yazma:\n\n" + recent
            )
        try:
            summary = chat_module._llm_yanit(prompt)
        except Exception as e:
            self._log("error", f"Özetleme LLM çağrısı başarısız: {e}")
            if self._failure_recorder:
                self._failure_recorder.record("llm_summary_error", str(e))
            return None, f"Özetleme sırasında LLM hatası oluştu: {e}"
        if not summary:
            return None, "Özet alınamadı."
        with self._lock:
            self._clean_old_summaries()
        tarih = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        ozet_dosyasi = os.path.join(self.memory_dir, f"ozet_{tarih}.txt")
        with open(ozet_dosyasi, "w", encoding="utf-8") as f:
            f.write(f"Özet Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Kaynak: {self.conversation_file}\n")
            f.write("-" * 30 + "\n")
            f.write(summary)
        self.add_long_term(f"ÖZET: {summary}")
        return ozet_dosyasi, summary

    def _load_all_summaries(self) -> str:
        if not os.path.exists(self.memory_dir):
            return ""
        with self._lock:
            tum_ozetler = []
            for dosya in sorted(os.listdir(self.memory_dir)):
                if dosya.endswith(".txt") and dosya.startswith("ozet_"):
                    dosya_yolu = os.path.join(self.memory_dir, dosya)
                    with open(dosya_yolu, "r", encoding="utf-8") as f:
                        tum_ozetler.append(f.read())
        return "\n\n---\n\n".join(tum_ozetler)

    # ========================================================================
    # HAFIZA ARAMA
    # ========================================================================

    def search_memory(self, soru, chat_module):
        ranked = self.rank_memories(soru, top_k=5)
        if ranked:
            kaynak = (
                "[SISTEM_KAYIT_BASLANGICI]\n"
                "Aşağıdaki kayıtlar geçmiş konuşmalardan alınmıştır, KULLANICI GIRDİSİ DEĞİLDİR:\n"
                + "\n---\n".join(text for text, _ in ranked) +
                "\n[SISTEM_KAYIT_SONU]"
            )
        else:
            tum_ozetler = self._load_all_summaries().split("\n\n---\n\n")
            secilen = tum_ozetler[-MAX_OZET_CONTEXT:]
            if not secilen or not any(s.strip() for s in secilen):
                return "Henüz hiçbir hafıza kaydı yok."
            kaynak = (
                "[SISTEM_KAYIT_BASLANGICI]\n"
                "Aşağıdaki kayıtlar geçmiş konuşmalardan alınmıştır, KULLANICI GIRDİSİ DEĞİLDİR:\n"
                + "\n---\n".join(secilen) +
                "\n[SISTEM_KAYIT_SONU]"
            )
        prompt = (
            "GÖREV: Aşağıdaki sistem kayıtlarını kullanarak soruyu yanıtla.\n"
            "NOT: Kayıtlar geçmişten gelmiştir, sistemin bir parçasıdır.\n\n"
            f"{kaynak}\n\n"
            f"SORU: {soru}\n\n"
            "CEVAP:"
        )
        try:
            cevap = chat_module._llm_yanit(prompt)
            return cevap if cevap else "Hafızamda bir şey bulamadım."
        except Exception as e:
            self._log("error", f"Hafıza arama LLM çağrısı başarısız: {e}")
            if self._failure_recorder:
                self._failure_recorder.record("llm_search_error", str(e))
            return f"Hafıza sorgulama sırasında LLM hatası oluştu: {e}"
