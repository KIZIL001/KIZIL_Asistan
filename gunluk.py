import os
from datetime import datetime

KLASOR = "gunlukler"

def bugunun_dosyasi():
    if not os.path.exists(KLASOR):
        os.mkdir(KLASOR)
    tarih = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(KLASOR, f"{tarih}.txt")

def yaz():
    dosya = bugunun_dosyasi()
    print(f"Bugünün günlüğü: {dosya}")
    print("Ne yazmak istersin? (Bitirince ENTER, sonra Ctrl+D)")
    satirlar = []
    try:
        while True:
            satir = input()
            satirlar.append(satir)
    except EOFError:
        pass
    with open(dosya, "a", encoding="utf-8") as f:
        f.write("\n".join(satirlar) + "\n")
    print("Kaydedildi.")

def oku():
    dosya = bugunun_dosyasi()
    if os.path.exists(dosya):
        print(f"--- {dosya} ---")
        with open(dosya, "r", encoding="utf-8") as f:
            print(f.read())
    else:
        print("Bugün için henüz not yok.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "oku":
        oku()
    else:
        yaz()
