from modules.chat.chat_module import ChatModule
from core.memory_manager import MemoryManager
from utils.logger import Logger
from utils.config import Config

def main():
    config = Config()
    logger = Logger(log_dir=config.STORAGE_DIR, log_file=config.LOG_FILE)
    logger.info("KIZIL Asistan başlatılıyor...")

    chat = ChatModule()
    memory = MemoryManager()

    logger.info("Modüller yüklendi.")
    logger.info(f"Depolama dizini: {config.STORAGE_DIR}")

    print("KIZIL Asistan başlatıldı.")
    print("Sohbet etmek için yaz, çıkmak için 'çık' ya da 'exit' yaz.\n")

    try:
        while True:
            try:
                girdi = input("Sen: ").strip()
            except (EOFError, KeyboardInterrupt):
                logger.info("Kullanıcı çıkış sinyali gönderdi.")
                break

            if girdi.lower() in ("çık", "exit", "quit", "q"):
                logger.info("Kullanıcı çıkış komutu girdi.")
                break

            # Hafızadan şu ana kadarki konuşma geçmişini al
            context = memory.get_context()

            # Cevabı üret
            cevap = chat.yanit_ver(girdi, context)
            print(f"KIZIL: {cevap}")

            # Yeni mesajları hafızaya ekle (önce kullanıcı, sonra asistan)
            memory.add_to_context("user", girdi)
            memory.add_to_context("assistant", cevap)

            # Dosyaya kaydet
            memory.save_conversation(girdi, cevap)
            logger.debug(f"Konuşma kaydedildi: {girdi} -> {cevap}")

    except Exception as e:
        logger.error(f"Beklenmeyen hata: {e}")

    finally:
        logger.info("KIZIL Asistan kapatılıyor.")
        print("Görüşmek üzere!")

if __name__ == "__main__":
    main()
