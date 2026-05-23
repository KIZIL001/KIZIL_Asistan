import os
from datetime import datetime
from modules.chat.chat_module import ChatModule

KONUSMALAR_DIZINI = os.path.join("storage", "conversations")
KONUSMA_DOSYASI = os.path.join(KONUSMALAR_DIZINI, "gunluk.txt")

def konusmayi_kaydet(girdi, cevap):
    os.makedirs(KONUSMALAR_DIZINI, exist_ok=True)
    with open(KONUSMA_DOSYASI, "a", encoding="utf-8") as f:
        zaman = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{zaman} | Kullanici: {girdi}\n")
        f.write(f"{zaman} | KIZIL: {cevap}\n")
        f.write("-" * 30 + "\n")

def main():
    chat = ChatModule()
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

        cevap = chat.yanit_ver(girdi)
        print(f"KIZIL: {cevap}")

        konusmayi_kaydet(girdi, cevap)

if __name__ == "__main__":
    main()
