import os
from datetime import datetime
from collections import deque
from utils.config import Config

class MemoryManager:
    """Konuşmaları ve kısa süreli hafızayı yönetir."""

    def __init__(self, storage_path=None, max_context=20):
        config = Config()
        self.storage_path = storage_path if storage_path else config.STORAGE_DIR
        self.conversations_dir = os.path.join(self.storage_path, config.CONVERSATIONS_DIR)
        self.conversation_file = os.path.join(self.conversations_dir, "gunluk.txt")
        os.makedirs(self.conversations_dir, exist_ok=True)

        # Kısa süreli hafıza: son N mesajı tutar (ilk giren ilk çıkar)
        self.context = deque(maxlen=max_context)

    def add_to_context(self, role, message):
        """Hafızaya bir mesaj ekle (role: 'user' veya 'assistant')."""
        self.context.append({"role": role, "content": message})

    def get_context(self):
        """Şu ana kadarki konuşma geçmişini liste olarak döndür."""
        return list(self.context)

    def save_conversation(self, user_input, response):
        """Bir konuşma satırını tarihle birlikte dosyaya ekler."""
        zaman = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.conversation_file, "a", encoding="utf-8") as f:
            f.write(f"{zaman} | Kullanici: {user_input}\n")
            f.write(f"{zaman} | KIZIL: {response}\n")
            f.write("-" * 30 + "\n")
