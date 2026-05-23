import os
from datetime import datetime

KONUSMALAR_DIZINI = os.path.join("storage", "conversations")
KONUSMA_DOSYASI = os.path.join(KONUSMALAR_DIZINI, "gunluk.txt")

def konusmayi_kaydet(girdi, cevap):
    """Her konuşmayı tarih saat ile dosyaya ekle."""
    os.makedirs(KONUSMALAR_DIZINI, exist_ok=True)
    with open(KONUSMA_DOSYASI, "a", encoding="utf-8") as f:
        zaman = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{zaman} | Kullanici: {girdi}\n")
        f.write(f"{zaman} | KIZIL: {cevap}\n")
        f.write("-" * 30 + "\n")

def yanit_ver(girdi):
    """Basit kural tabanlı yanıt üreticisi. İleride gerçek zeka ile değişecek."""
    girdi = girdi.strip().lower()
    if not girdi:
        return "Bir şey demedin, tekrar dene."
    if "merhaba" in girdi or "selam" in girdi:
        return "Merhaba! Nasıl yardımcı olabilirim?"
    if "nasılsın" in girdi:
        return "Ben bir yazılımım, yorulmam. Ama sana yardım etmek için sabırsızlanıyorum!"
    if "hava" in girdi:
        return "Hava durumu modülü henüz eklenmedi, ama ileride hava durumunu da söyleyeceğim."
    if "teşekkür" in girdi or "sağol" in girdi:
        return "Rica ederim, ne zaman istersen buradayım."
    return "Henüz tam olarak anlayamadım. Biraz daha basit sormayı dene ya da 'yardım' yaz."

def main():
    print("KIZIL Asistan başlatıldı.")
    print("Sohbet etmek için yaz, çıkmak için 'çık' ya da 'exit' yaz.\n")

    while True:
        try:
            girdi = input("Sen: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nKapatılıyor...")
            break

        if girdi.lower() in ("çık", "exit", "quit", "q"):
            print("Görüşmek üzere!")
            break

        cevap = yanit_ver(girdi)
        print(f"KIZIL: {cevap}")

        # Konuşmayı kaydet
        konusmayi_kaydet(girdi, cevap)

if __name__ == "__main__":
    main()
