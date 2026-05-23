import os
from datetime import datetime
from collections import deque
from utils.config import Config

class MemoryManager:
    """Konuşmaları ve kısa/uzun süreli hafızayı yönetir."""

    def __init__(self, storage_path=None, max_context=20):
        config = Config()
        self.storage_path = storage_path if storage_path else config.STORAGE_DIR
        self.conversations_dir = os.path.join(self.storage_path, config.CONVERSATIONS_DIR)
        self.memory_dir = os.path.join(self.storage_path, config.MEMORY_DIR)
        self.conversation_file = os.path.join(self.conversations_dir, "gunluk.txt")
        os.makedirs(self.conversations_dir, exist_ok=True)
        os.makedirs(self.memory_dir, exist_ok=True)

        self.context = deque(maxlen=max_context)

    def add_to_context(self, role, message):
        self.context.append({"role": role, "content": message})

    def get_context(self):
        return list(self.context)

    def save_conversation(self, user_input, response):
        zaman = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.conversation_file, "a", encoding="utf-8") as f:
            f.write(f"{zaman} | Kullanici: {user_input}\n")
            f.write(f"{zaman} | KIZIL: {response}\n")
            f.write("-" * 30 + "\n")

    def _read_last_lines(self, max_lines=50):
        """Günlük dosyasının son N satırını okur."""
        if not os.path.exists(self.conversation_file):
            return ""
        with open(self.conversation_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return "".join(lines[-max_lines:])

    def summarize_and_save(self, model_name, chat_module):
        """
        Son konuşmaları okur, özetini LLM'den alır ve memory dizinine kaydeder.
        chat_module: ChatModule örneği (yanıt_ver metodu ile çağırmak yerine doğrudan LLM kullanacak)
        model_name: kullanılacak model adı
        """
        config = Config()
        recent_text = self._read_last_lines(max_lines=config.SUMMARY_MAX_LINES)
        if not recent_text.strip():
            return None, "Henüz kayıtlı konuşma yok."

        # Özetleme için LLM'e sor
        prompt = f"Aşağıdaki konuşma kaydından önemli noktaları, alınan kararları ve kullanıcı hakkında edinilen bilgileri kısa bir özet halinde çıkar. Sadece özeti yaz, başka bir şey yazma:\n\n{recent_text}"
        try:
            summary = chat_module._llm_yanit(prompt)
        except Exception as e:
            return None, f"Özetleme hatası: {e}"

        if not summary:
            return None, "Özet alınamadı."

        # Özeti dosyaya kaydet
        tarih = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        ozet_dosyasi = os.path.join(self.memory_dir, f"ozet_{tarih}.txt")
        with open(ozet_dosyasi, "w", encoding="utf-8") as f:
            f.write(f"Özet Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Kaynak: {self.conversation_file}\n")
            f.write("-" * 30 + "\n")
            f.write(summary)

        return ozet_dosyasi, summary
