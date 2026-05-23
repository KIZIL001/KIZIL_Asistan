from modules.chat.chat_module import ChatModule
from core.llm_router import LLMRouter
from modules.tasks.task_manager import TaskManager
from core.memory_manager import MemoryManager
from modules.session.session_manager import SessionManager
from utils.logger import Logger
from utils.config import Config


class Orchestrator:
    def __init__(self, debug_mode=False):
        self.config = Config()
        self.logger = Logger(
            log_dir=self.config.STORAGE_DIR,
            log_file=self.config.LOG_FILE,
            log_level=self.config.LOG_LEVEL,
            debug_mode=debug_mode,
        )
        self.router = LLMRouter(model=self.config.LLM_MODEL)
        self.chat = ChatModule(router=self.router)
        self.memory = MemoryManager()
        self.task_mgr = TaskManager(storage_dir=self.config.STORAGE_DIR)
        self.session = SessionManager(storage_dir=self.config.STORAGE_DIR)
        self.running = False

    # ---------- ana döngü ----------

    def start(self):
        self.running = True
        self.session.start_session()
        self.logger.info("KIZIL Asistan başlatılıyor...")
        print("KIZIL Asistan başlatıldı.")
        print("Komutlar için 'yardım' yazabilirsin.\n")
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
        try:
            komut = girdi.lower()
            if komut in ("çık", "exit", "quit", "q"):
                self.stop()
            elif komut in ("yardım", "yardim", "help", "h"):
                self._help()
            elif komut == "özetle":
                self._summary()
            elif komut.startswith("hatırla "):
                user_msg, resp = self._remember(girdi)
                if resp is not None:
                    self._save(user_msg, resp)
            elif komut.startswith("görev ekle "):
                self._task_add(girdi)
            elif komut in ("görevler", "görev listesi"):
                self._task_list()
            elif komut.startswith("görev sil "):
                self._task_del(girdi)
            elif komut.startswith("görev tamam "):
                self._task_done(girdi)
            else:
                user_msg, resp = self._chat(girdi)
                if resp is not None:
                    self._save(user_msg, resp)
        except Exception as e:
            self.logger.error(f"İşlem hatası: {e}")
            print("KIZIL: Bir hata oluştu. Lütfen tekrar dene.")

    def _save(self, user_msg, resp):
        self.memory.save_conversation(user_msg, resp)
        self.memory.add_to_context("user", user_msg)
        self.memory.add_to_context("assistant", resp)

    # ---------- yardım ----------

    def _help(self):
        print("""
KIZIL Asistan - Komut Listesi
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
sohbet için direkt yaz        → merhaba, nasılsın
çık, exit, quit, q            → asistanı kapat
yardım, help, h               → bu listeyi göster
özetle                        → konuşma özeti çıkar
hatırla <soru>                → hafızadan sorgula
görev ekle <açıklama>         → yeni görev ekle
görevler                      → görevleri listele
görev sil <no>                → görevi sil
görev tamam <no>              → görevi tamamlandı işaretle
        """.strip())

    # ---------- LLM sarmalayıcı ----------

    def _safe_llm(self, func, *args):
        try:
            return func(*args)
        except ConnectionError:
            print("KIZIL: LLM baglantisi kurulamadi.")
            print("  -> Ollama calisiyor mu? (http://localhost:11434)")
            print("  -> Model yuklu mu? 'ollama list' ile kontrol et.")
            return None
        except Exception as e:
            self.logger.error(f"LLM hatasi: {e}")
            print(f"KIZIL: LLM cagrisi sirasinda hata olustu.")
            print(f"  -> Hata: {e}")
            return None

    # ---------- sohbet ----------

    def _chat(self, msg):
        def istek():
            ctx = self.memory.get_context()
            resp = self.chat.yanit_ver(msg, ctx)
            print("KIZIL:", resp)
            return resp

        resp = self._safe_llm(istek)
        return msg, resp

    # ---------- özet ----------

    def _summary(self):
        def istek():
            f, s = self.memory.summarize_and_save(self.router.model, self.chat)
            if f:
                print(f"KIZIL: Özet kaydedildi: {f}")
                print("Özet:", s)
            else:
                print("KIZIL:", s)
            return s

        self._safe_llm(istek)

    # ---------- hafıza ----------

    def _remember(self, girdi):
        q = girdi[8:].strip()
        if not q:
            print("KIZIL: Ne hakkında hatırlatma yapmamı istersin?")
            return girdi, None

        def istek():
            a = self.memory.search_memory(q, self.chat)
            print("KIZIL:", a)
            return a

        resp = self._safe_llm(istek)
        return girdi, resp

    # ---------- görevler ----------

    def _task_add(self, girdi):
        desc = girdi[11:].strip()
        if not desc:
            print("KIZIL: Örnek: görev ekle markete git")
            return
        try:
            t = self.task_mgr.add_task(desc)
            print(f"KIZIL: Görev eklendi: [{t['id']}] {t['desc']}")
        except Exception as e:
            self.logger.error(f"Görev ekleme hatası: {e}")
            print("KIZIL: Görev eklenemedi.")

    def _task_list(self):
        try:
            tasks = self.task_mgr.list_tasks()
            if not tasks:
                print("KIZIL: Henüz görev yok.")
                return
            for t in tasks:
                durum = "✓" if t.get("done") else "☐"
                print(f"  {durum} [{t['id']}] {t['desc']}")
        except Exception as e:
            self.logger.error(f"Görev listeleme hatası: {e}")
            print("KIZIL: Görevler listelenemedi.")

    def _task_del(self, girdi):
        try:
            gid = girdi[10:].strip()
            ok = self.task_mgr.delete_task(gid)
            print(f"KIZIL: Görev #{gid} silindi." if ok else f"KIZIL: Görev #{gid} bulunamadı.")
        except Exception as e:
            self.logger.error(f"Görev silme hatası: {e}")
            print("KIZIL: Görev silinirken hata oluştu.")

    def _task_done(self, girdi):
        try:
            gid = girdi[12:].strip()
            ok = self.task_mgr.mark_done(gid)
            print(f"KIZIL: Görev #{gid} tamamlandı." if ok else f"KIZIL: Görev #{gid} bulunamadı.")
        except Exception as e:
            self.logger.error(f"Görev tamamlama hatası: {e}")
            print("KIZIL: Görev tamamlanırken hata oluştu.")

    # ---------- kapanış ----------

    def stop(self):
        self.session.end_session()
        self.running = False
        self.logger.info("KIZIL Asistan kapatılıyor.")
        print("Görüşmek üzere!")
