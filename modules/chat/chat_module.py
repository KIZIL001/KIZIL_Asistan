import ollama
from utils.config import Config

class ChatModule:
    """Ollama tabanlı sohbet modülü. Kısa süreli hafıza (context) kullanır."""

    def __init__(self, model=None):
        self.config = Config()
        self.model = model if model else self.config.LLM_MODEL

    def _llm_yanit(self, mesaj, context=None):
        """Ollama modeline soru sor ve cevabı döndür. Geçmiş sohbeti context olarak ekler."""
        try:
            messages = []
            if context:
                messages.extend(context)  # önceki konuşmaları ekle
            messages.append({"role": "user", "content": mesaj})

            response = ollama.chat(
                model=self.model,
                messages=messages
            )
            return response["message"]["content"].strip()
        except Exception as e:
            print(f"(Uyarı: LLM hatası - {e}. Varsayılan yanıt kullanılıyor.)")
            return None

    def yanit_ver(self, girdi: str, context=None) -> str:
        if not girdi or not girdi.strip():
            return "Bir şey demedin, tekrar dene."

        cevap = self._llm_yanit(girdi, context)
        if cevap:
            return cevap

        # Yedek basit yanıtlar
        girdi = girdi.strip().lower()
        if "merhaba" in girdi or "selam" in girdi:
            return "Merhaba! Nasıl yardımcı olabilirim?"
        if "nasılsın" in girdi:
            return "Ben bir yazılımım, yorulmam. Ama sana yardım etmek için sabırsızlanıyorum!"
        if "hava" in girdi:
            return "Hava durumu modülü henüz eklenmedi, ama ileride hava durumunu da söyleyeceğim."
        if "teşekkür" in girdi or "sağol" in girdi:
            return "Rica ederim, ne zaman istersen buradayım."
        return self.config.DEFAULT_UNKNOWN_RESPONSE
