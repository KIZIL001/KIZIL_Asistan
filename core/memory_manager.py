import os
from datetime import datetime

class MemoryManager:
    """Konuşmaları ve ileride diğer hafıza verilerini yönetir."""

    def __init__(self, storage_path="storage"):
        self.storage_path = storage_path
        self.conversations_dir = os.path.join(storage_path, "conversations")
        self.conversation_file = os.path.join(self.conversations_dir, "gunluk.txt")
        os.makedirs(self.conversations_dir, exist_ok=True)

    def save_conversation(self, user_input, response):
        """Bir konuşma satırını tarihle birlikte dosyaya ekler."""
        zaman = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.conversation_file, "a", encoding="utf-8") as f:
            f.write(f"{zaman} | Kullanici: {user_input}\n")
            f.write(f"{zaman} | KIZIL: {response}\n")
            f.write("-" * 30 + "\n")
