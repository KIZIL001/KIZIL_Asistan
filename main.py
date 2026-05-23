from modules.chat.chat_module import ChatModule
from core.memory_manager import MemoryManager
from utils.logger import Logger
from utils.config import Config

def main():
    config = Config()
    logger = Logger(log_dir=config.STORAGE_DIR, log_file=config.LOG_FILE)
    logger.info("KIZIL Asistan başlatılıyor...")

    chat = ChatModule()
    memory = MemoryManager(storage_path=config.STORAGE_DIR)

    logger.info("Modüller yüklendi.")
    logger.info(f"Depolama dizini: {config.STORAGE_DIR}")
    logger.debug(f"Log dosyası: {config.LOG_FILE}")

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

            cevap = chat.yanit_ver(girdi)
            print(f"KIZIL: {cevap}")

            memory.save_conversation(girdi, cevap)
            logger.debug(f"Konuşma kaydedildi: {girdi} -> {cevap}")

    except Exception as e:
        logger.error(f"Beklenmeyen hata: {e}")

    finally:
        logger.info("KIZIL Asistan kapatılıyor.")
        print("Görüşmek üzere!")

if __name__ == "__main__":
    main()
