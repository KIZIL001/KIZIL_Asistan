import ollama
from utils.config import Config

class ChatModule:
    """Ollama tabanlı sohbet modülü. Hata durumunda basit yanıtlar üretir."""

    def __init__(self, model=None):
        self.config = Config()
        self.model = model if model else self.config.LLM_MODEL

    def _llm_yanit(self, mesaj):
        """Ollama modeline soru sor ve cevabı döndür."""
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": mesaj}]
            )
            return response["message"]["content"].strip()
        except Exception as e:
            # Ollama çalışmıyorsa ya da başka hata varsa fallback
            print(f"(Uyarı: LLM hatası - {e}. Varsayılan yanıt kullanılıyor.)")
            return None

    def yanit_ver(self, girdi: str) -> str:
        if not girdi or not girdi.strip():
            return "Bir şey demedin, tekrar dene."

        # Önce yapay zekâya sor
        cevap = self._llm_yanit(girdi)
        if cevap:
            return cevap

        # Yapay zekâ cevap veremediyse basit yedek kurallara dön
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
