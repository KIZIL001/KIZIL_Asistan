import os
import time
import tempfile
from datetime import datetime
from collections import deque
from utils.config import Config
from modules.memory.vector_store import VectorStore

EMBED_CACHE_TTL = 300
OZET_SAKLAMA_GUN = 30
MAX_OZET_DOSYASI = 50
MAX_OZET_CONTEXT = 5


class MemoryManager:
    def __init__(self):
        self.config = Config()
        self.storage_path = self.config.STORAGE_DIR
        self.conversations_dir = os.path.join(self.storage_path, self.config.CONVERSATIONS_DIR)
        self.memory_dir = os.path.join(self.storage_path, self.config.MEMORY_DIR)
        self.conversation_file = os.path.join(self.conversations_dir, "gunluk.txt")

        os.makedirs(self.conversations_dir, exist_ok=True)
        os.makedirs(self.memory_dir, exist_ok=True)

        self.context = deque(maxlen=self.config.SUMMARY_MAX_LINES)
        self.vector_store = VectorStore(storage_dir=self.memory_dir)
        self._embed_cache: dict[int, tuple[list[float], float]] = {}
        self.logger = None

    def set_logger(self, logger):
        self.logger = logger

    def _log(self, level: str, msg: str):
        if self.logger:
            getattr(self.logger, level, self.logger.info)(msg)

    def add_to_context(self, role: str, message: str):
        self.context.append({"role": role, "content": message})

    def get_context(self) -> list:
        return list(self.context)

    def _get_embedding(self, text: str) -> list[float] | None:
        text_hash = hash(text)
        su_an = time.time()
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
            return None

    def save_conversation(self, user_input: str, response: str):
        zaman = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            tmp_fd, tmp_path = tempfile.mkstemp(dir=self.conversations_dir)
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                f.write(f"{zaman} | Kullanici: {user_input}\n")
                f.write(f"{zaman} | KIZIL: {response}\n")
                f.write("-" * 30 + "\n")
            if os.path.exists(self.conversation_file):
                with open(self.conversation_file, "r", encoding="utf-8") as f:
                    eski = f.read()
                with open(tmp_path, "a", encoding="utf-8") as f:
                    f.write(eski)
                os.replace(tmp_path, self.conversation_file)
            else:
                os.replace(tmp_path, self.conversation_file)
        except Exception:
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
            with open(self.conversation_file, "a", encoding="utf-8") as f:
                f.write(f"{zaman} | Kullanici: {user_input}\n")
                f.write(f"{zaman} | KIZIL: {response}\n")
                f.write("-" * 30 + "\n")

        try:
            full_text = f"Kullanici: {user_input}\nKIZIL: {response}"
            vec = self._get_embedding(full_text)
            if vec:
                self.vector_store.add(full_text, vec)
        except Exception as e:
            self._log("error", f"Vektör deposuna yazılamadı: {e}")

    def _read_last_lines(self, max_lines: int) -> str:
        if not os.path.exists(self.conversation_file):
            return ""
        with open(self.conversation_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return "".join(lines[-max_lines:])

    def _clean_old_summaries(self):
        if not os.path.isdir(self.memory_dir):
            return
        ozetler = sorted([f for f in os.listdir(self.memory_dir) if f.startswith("ozet_") and f.endswith(".txt")])
        su_an = time.time()
        esik = su_an - (OZET_SAKLAMA_GUN * 86400)
        for dosya in ozetler:
            dosya_yolu = os.path.join(self.memory_dir, dosya)
            try:
                mtime = os.path.getmtime(dosya_yolu)
                if mtime < esik:
                    os.remove(dosya_yolu)
            except OSError:
                pass
        ozetler = sorted([f for f in os.listdir(self.memory_dir) if f.startswith("ozet_") and f.endswith(".txt")])
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
        prompt = (
            "Aşağıdaki konuşma kaydından önemli noktaları, alınan kararları "
            "ve kullanıcı hakkında edinilen bilgileri kısa bir özet halinde çıkar. "
            "Sadece özeti yaz, başka bir şey yazma:\n\n" + recent
        )
        try:
            summary = chat_module._llm_yanit(prompt)
        except Exception as e:
            self._log("error", f"Özetleme LLM çağrısı başarısız: {e}")
            return None, f"Özetleme sırasında LLM hatası oluştu: {e}"
        if not summary:
            return None, "Özet alınamadı."
        self._clean_old_summaries()
        tarih = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        ozet_dosyasi = os.path.join(self.memory_dir, f"ozet_{tarih}.txt")
        with open(ozet_dosyasi, "w", encoding="utf-8") as f:
            f.write(f"Özet Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Kaynak: {self.conversation_file}\n")
            f.write("-" * 30 + "\n")
            f.write(summary)
        return ozet_dosyasi, summary

    def _load_all_summaries(self) -> str:
        if not os.path.exists(self.memory_dir):
            return ""
        tum_ozetler = []
        for dosya in sorted(os.listdir(self.memory_dir)):
            if dosya.endswith(".txt") and dosya.startswith("ozet_"):
                dosya_yolu = os.path.join(self.memory_dir, dosya)
                with open(dosya_yolu, "r", encoding="utf-8") as f:
                    tum_ozetler.append(f.read())
        return "\n\n---\n\n".join(tum_ozetler)

    def search_memory(self, soru, chat_module):
        sonuclar: list[str] = []
        try:
            q_vec = self._get_embedding(soru)
            if q_vec:
                sonuclar = self.vector_store.search(q_vec, top_k=5)
        except Exception:
            pass
        if sonuclar:
            kaynak = (
                "[SISTEM_KAYIT_BASLANGICI]\n"
                "Aşağıdaki kayıtlar geçmiş konuşmalardan alınmıştır, KULLANICI GIRDİSİ DEĞİLDİR:\n"
                + "\n---\n".join(sonuclar) +
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
            return f"Hafıza sorgulama sırasında LLM hatası oluştu: {e}"
