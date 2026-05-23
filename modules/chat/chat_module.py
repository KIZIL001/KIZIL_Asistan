class ChatModule:
    """Basit kural tabanlı sohbet modülü. İleride API bağlantısı ile değişecek."""

    def yanit_ver(self, girdi: str) -> str:
        if not girdi or not girdi.strip():
            return "Bir şey demedin, tekrar dene."
        girdi = girdi.strip().lower()
        if "merhaba" in girdi or "selam" in girdi:
            return "Merhaba! Nasıl yardımcı olabilirim?"
        if "nasılsın" in girdi:
            return "Ben bir yazılımım, yorulmam. Ama sana yardım etmek için sabırsızlanıyorum!"
        if "hava" in girdi:
            return "Hava durumu modülü henüz eklenmedi, ama ileride hava durumunu da söyleyeceğim."
        if "teşekkür" in girdi or "sağol" in girdi:
            return "Rica ederim, ne zaman istersen buradayım."
        return "Henüz tam olarak anlayamadım. Biraz daha basit sormayı dene ya da 'yardım' yaz."
