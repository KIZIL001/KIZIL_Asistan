from modules.chat.chat_module import ChatModule
from core.memory_manager import MemoryManager

def main():
    chat = ChatModule()
    memory = MemoryManager()

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

        memory.save_conversation(girdi, cevap)

if __name__ == "__main__":
    main()
