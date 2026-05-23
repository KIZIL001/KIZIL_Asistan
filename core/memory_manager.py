import os
from datetime import datetime
from collections import deque
from utils.config import Config


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

    def add_to_context(self, role: str, message: str):
        self.context.append({"role": role, "content": message})

    def get_context(self) -> list:
        return list(self.context)

    def save_conversation(self, user_input: str, response: str):
        zaman = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.conversation_file, "a", encoding="utf-8") as f:
            f.write(f"{zaman} | Kullanici: {user_input}\n")
            f.write(f"{zaman} | KIZIL: {response}\n")
            f.write("-" * 30 + "\n")

    def _read_last_lines(self, max_lines: int) -> str:
        if not os.path.exists(self.conversation_file):
            return ""
        with open(self.conversation_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return "".join(lines[-max_lines:])

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
            return None, f"Özetleme hatası: {e}"

        if not summary:
            return None, "Özet alınamadı."

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
            if dosya.endswith(".txt"):
                dosya_yolu = os.path.join(self.memory_dir, dosya)
                with open(dosya_yolu, "r", encoding="utf-8") as f:
                    tum_ozetler.append(f.read())
        return "\n\n---\n\n".join(tum_ozetler)

    def search_memory(self, soru, chat_module):
        tum_metin = self._load_all_summaries()
        if not tum_metin.strip():
            return "Henüz hiçbir özet kaydedilmemiş. Önce 'özetle' komutunu kullanmalısın."

        prompt = (
            "Aşağıda geçmiş konuşmalara ait özetler bulunuyor. "
            "Bu özetlere dayanarak kullanıcının sorusuna kısa ve net bir cevap ver.\n\n"
            "--- ÖZETLER ---\n" + tum_metin + "\n\n--- SORU ---\n" + soru + "\n\nCevap:"
        )

        try:
            cevap = chat_module._llm_yanit(prompt)
            return cevap if cevap else "Hafızamda bir şey bulamadım."
        except Exception as e:
            return f"Hafıza sorgulama hatası: {e}"
