from modules.chat.chat_module import ChatModule
from core.llm_router import LLMRouter
from modules.tasks.task_manager import TaskManager
from core.memory_manager import MemoryManager
from utils.logger import Logger
from utils.config import Config

class Orchestrator:
    """Tüm modülleri yönetir ve kullanıcı etkileşimini sağlar (hata yönetimi güçlendirildi)."""

    def __init__(self):
        self.config = Config()
        self.logger = Logger(log_dir=self.config.STORAGE_DIR, log_file=self.config.LOG_FILE)
        self.router = LLMRouter(model=self.config.LLM_MODEL)
        self.chat = ChatModule(router=self.router)
        self.memory = MemoryManager()
        self.task_mgr = TaskManager(storage_dir=self.config.STORAGE_DIR)
        self.running = False

    def start(self):
        self.running = True
        self.logger.info("KIZIL Asistan başlatılıyor...")
        self.logger.info("Modüller yüklendi.")
        print("KIZIL Asistan başlatıldı.")
        print("Sohbet et, çık/exit ile çık.")
        print("Komutlar: özetle, hatırla <soru>, görev ekle <açıklama>, görevler, görev sil <no>, görev tamam <no>")
        while self.running:
            try:
                girdi = input("Sen: ").strip()
            except (EOFError, KeyboardInterrupt):
                self.stop()
                break
            if not girdi:
                continue
            self._process(girdi)

    def _process(self, girdi):
        """Gelen komutu ayır ve ilgili işleme yönlendir."""
        try:
            if girdi.lower() in ("çık", "exit", "quit", "q"):
                self.stop()
            elif girdi.lower() == "özetle":
                self._summary()
            elif girdi.lower().startswith("hatırla"):
                self._remember(girdi)
            elif girdi.lower().startswith("görev ekle"):
                self._task_add(girdi)
            elif girdi.lower() in ("görevler", "görev listesi"):
                self._task_list()
            elif girdi.lower().startswith("görev sil"):
                self._task_del(girdi)
            elif girdi.lower().startswith("görev tamam"):
                self._task_done(girdi)
            else:
                self._chat(girdi)
        except Exception as e:
            self.logger.error(f"Komut işlenirken hata: {e}")
            print(f"KIZIL: Üzgünüm, bir hata oluştu. Lütfen tekrar dener misin? (Hata: {e})")

    def _chat(self, msg):
        try:
            ctx = self.memory.get_context()
            resp = self.chat.yanit_ver(msg, ctx)
            print("KIZIL:", resp)
            self.memory.add_to_context("user", msg)
            self.memory.add_to_context("assistant", resp)
            self.memory.save_conversation(msg, resp)
        except ConnectionError:
            print("KIZIL: LLM bağlantısı şu anda kurulamıyor. Lütfen Ollama'nın çalıştığından emin ol.")
        except Exception as e:
            self.logger.error(f"Sohbet hatası: {e}")
            print(f"KIZIL: Sohbet sırasında beklenmeyen bir hata oluştu: {e}")

    def _summary(self):
        try:
            f, s = self.memory.summarize_and_save(self.config.LLM_MODEL, self.chat)
            if f:
                print("KIZIL: Özet kaydedildi:", f)
                print("Özet:", s)
            else:
                print("KIZIL:", s)
        except Exception as e:
            self.logger.error(f"Özetleme hatası: {e}")
            print(f"KIZIL: Özetleme sırasında hata oluştu: {e}")

    def _remember(self, girdi):
        q = girdi[7:].strip()
        if not q:
            print("KIZIL: Ne hakkında hatırlatma yapmamı istersin?")
            return
        try:
            a = self.memory.search_memory(q, self.chat)
            print("KIZIL:", a)
            self.memory.add_to_context("user", girdi)
            self.memory.add_to_context("assistant", a)
            self.memory.save_conversation(girdi, a)
        except Exception as e:
            self.logger.error(f"Hafıza sorgulama hatası: {e}")
            print(f"KIZIL: Hafıza sorgulanırken hata oluştu: {e}")

    def _task_add(self, girdi):
        desc = girdi[11:].strip()
        if not desc:
            print("KIZIL: Örnek: görev ekle markete git")
            return
        try:
            t = self.task_mgr.add_task(desc)
            print(f"KIZIL: Görev eklendi: [{t['id']}] {t['description']}")
            self.memory.add_to_context("user", girdi)
            self.memory.add_to_context("assistant", f"Görev eklendi: {t['description']}")
            self.memory.save_conversation(girdi, f"Görev eklendi: {t['description']}")
        except Exception as e:
            self.logger.error(f"Görev ekleme hatası: {e}")
            print(f"KIZIL: Görev eklenemedi: {e}")

    def _task_list(self):
        try:
            lst = self.task_mgr.list_tasks()
            print("KIZIL:\n" + lst)
            self.memory.add_to_context("user", "görevler")
            self.memory.add_to_context("assistant", lst)
            self.memory.save_conversation("görevler", lst)
        except Exception as e:
            self.logger.error(f"Görev listeleme hatası: {e}")
            print(f"KIZIL: Görevler listelenemedi: {e}")

    def _task_del(self, girdi):
        try:
            gid = girdi.split()[-1]
            r = self.task_mgr.delete_task(gid)
            print("KIZIL:", r)
            self.memory.add_to_context("user", girdi)
            self.memory.add_to_context("assistant", r)
            self.memory.save_conversation(girdi, r)
        except Exception as e:
            self.logger.error(f"Görev silme hatası: {e}")
            print("KIZIL: Görev silinirken hata oluştu. Lütfen geçerli bir numara girdiğinden emin ol.")

    def _task_done(self, girdi):
        try:
            gid = girdi.split()[-1]
            r = self.task_mgr.mark_done(gid)
            print("KIZIL:", r)
            self.memory.add_to_context("user", girdi)
            self.memory.add_to_context("assistant", r)
            self.memory.save_conversation(girdi, r)
        except Exception as e:
            self.logger.error(f"Görev tamamlama hatası: {e}")
            print("KIZIL: Görev tamamlanırken hata oluştu. Lütfen geçerli bir numara girdiğinden emin ol.")

    def stop(self):
        self.running = False
        self.logger.info("KIZIL Asistan kapatılıyor.")
        print("Görüşmek üzere!")
