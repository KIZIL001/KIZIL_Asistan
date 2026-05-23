from modules.chat.chat_module import ChatModule
from core.memory_manager import MemoryManager
from modules.tasks.task_manager import TaskManager
from utils.logger import Logger
from utils.config import Config

def main():
    config = Config()
    logger = Logger(log_dir=config.STORAGE_DIR, log_file=config.LOG_FILE)
    logger.info("KIZIL Asistan başlatılıyor...")

    chat = ChatModule()
    memory = MemoryManager()
    task_mgr = TaskManager(storage_dir=config.STORAGE_DIR)

    logger.info("Modüller yüklendi.")

    print("KIZIL Asistan başlatıldı.")
    print("Sohbet etmek için yaz, çıkmak için 'çık' ya da 'exit' yaz.")
    print("Özel komutlar: özetle, hatırla <soru>, görev ekle <açıklama>, görevler, görev sil <no>, görev tamam <no>\n")

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

            # --- ÖZEL KOMUTLAR ---

            # Özetleme
            if girdi.lower() == "özetle":
                logger.info("Özetleme başlatıldı.")
                dosya, sonuc = memory.summarize_and_save(config.LLM_MODEL, chat)
                if dosya:
                    print(f"KIZIL: Özet kaydedildi: {dosya}")
                    print(f"Özet: {sonuc}")
                else:
                    print(f"KIZIL: {sonuc}")
                continue

            # Hafıza sorgulama
            if girdi.lower().startswith("hatırla"):
                soru = girdi[7:].strip()
                if not soru:
                    print("KIZIL: Ne hakkında hatırlatma yapmamı istersin?")
                    continue
                cevap = memory.search_memory(soru, chat)
                print(f"KIZIL: {cevap}")
                memory.add_to_context("user", girdi)
                memory.add_to_context("assistant", cevap)
                memory.save_conversation(girdi, cevap)
                continue

            # Görev ekle
            if girdi.lower().startswith("görev ekle"):
                aciklama = girdi[11:].strip()
                if not aciklama:
                    print("KIZIL: Ne görevi eklememi istersin? Örnek: görev ekle markete git")
                    continue
                task = task_mgr.add_task(aciklama)
                print(f"KIZIL: Görev eklendi: [{task['id']}] {task['description']}")
                memory.add_to_context("user", girdi)
                memory.add_to_context("assistant", f"Görev eklendi: {task['description']}")
                memory.save_conversation(girdi, f"Görev eklendi: {task['description']}")
                continue

            # Görev listele
            if girdi.lower() == "görevler" or girdi.lower() == "görev listesi":
                liste = task_mgr.list_tasks()
                print(f"KIZIL:\n{liste}")
                memory.add_to_context("user", girdi)
                memory.add_to_context("assistant", liste)
                memory.save_conversation(girdi, liste)
                continue

            # Görev sil
            if girdi.lower().startswith("görev sil"):
                try:
                    gid = girdi.split()[-1]
                    sonuc = task_mgr.delete_task(gid)
                except:
                    sonuc = "Kullanım: görev sil <numara>"
                print(f"KIZIL: {sonuc}")
                memory.add_to_context("user", girdi)
                memory.add_to_context("assistant", sonuc)
                memory.save_conversation(girdi, sonuc)
                continue

            # Görev tamamla
            if girdi.lower().startswith("görev tamam"):
                try:
                    gid = girdi.split()[-1]
                    sonuc = task_mgr.mark_done(gid)
                except:
                    sonuc = "Kullanım: görev tamam <numara>"
                print(f"KIZIL: {sonuc}")
                memory.add_to_context("user", girdi)
                memory.add_to_context("assistant", sonuc)
                memory.save_conversation(girdi, sonuc)
                continue

            # --- NORMAL SOHBET ---
            context = memory.get_context()
            cevap = chat.yanit_ver(girdi, context)
            print(f"KIZIL: {cevap}")

            memory.add_to_context("user", girdi)
            memory.add_to_context("assistant", cevap)
            memory.save_conversation(girdi, cevap)
            logger.debug(f"Konuşma kaydedildi: {girdi} -> {cevap}")

    except Exception as e:
        logger.error(f"Beklenmeyen hata: {e}")

    finally:
        logger.info("KIZIL Asistan kapatılıyor.")
        print("Görüşmek üzere!")

if __name__ == "__main__":
    main()
