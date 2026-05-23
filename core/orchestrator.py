import os
from datetime import datetime
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
            elif komut == "sıfırla":
                self._reset_context()
            elif komut == "hatalar":
                self._show_errors()
            elif komut == "oturumlar":
                self._show_sessions()
            elif komut == "dışa aktar":
                self._export_conversation()
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
            elif komut.startswith("model "):
                self._change_model(girdi)
            elif komut.startswith("ayar"):
                self._config_cmd(girdi)
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
sıfırla                       → konuşma geçmişini temizle
hatırla <soru>                → hafızadan sorgula
görev ekle <açıklama>         → yeni görev ekle
görevler                      → görevleri listele
görev sil <no>                → görevi sil
görev tamam <no>              → görevi tamamlandı işaretle
model <model_adi>             → LLM modelini değiştir
ayar                          → tüm ayarları listele
ayar <anahtar>                → anahtarın değerini göster
ayar <anahtar> <değer>        → anahtarı güncelle
ayar sıfırla                  → tüm ayarları varsayılana döndür
hatalar                       → son hata loglarını göster
oturumlar                     → geçmiş oturumları listele
dışa aktar                    → konuşma günlüğünü dışa aktar
        """.strip())

    # ---------- konuşma geçmişini temizle ----------

    def _reset_context(self):
        self.memory.context.clear()
        print("KIZIL: Konuşma geçmişi temizlendi.")

    # ---------- hata loglarını göster ----------

    def _show_errors(self):
        log_path = os.path.join(self.config.STORAGE_DIR, self.config.LOG_FILE)
        if not os.path.exists(log_path):
            print("KIZIL: Henüz log dosyası oluşmamış.")
            return
        with open(log_path, "r", encoding="utf-8") as f:
            lines = [line for line in f.readlines() if "[ERROR]" in line]
        if not lines:
            print("KIZIL: Hiç hata kaydı bulunamadı.")
            return
        print("KIZIL: Son 10 hata kaydı:")
        for line in lines[-10:]:
            print(f"  {line.strip()}")

    # ---------- oturum geçmişi ----------

    def _show_sessions(self):
        sessions = self.session.list_sessions()
        if not sessions:
            print("KIZIL: Henüz oturum kaydı yok.")
            return
        print("KIZIL: Geçmiş oturumlar:")
        for s in sessions:
            durum = "✅" if s.get("end") else "🔄"
            print(f"  {durum} {s['id']} | {s['start']} → {s.get('end', 'devam ediyor')}")

    # ---------- konuşma dışa aktar ----------

    def _export_conversation(self):
        src = self.memory.conversation_file
        if not os.path.exists(src):
            print("KIZIL: Dışa aktarılacak konuşma günlüğü bulunamadı.")
            return
        tarih = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = os.path.join(self.config.STORAGE_DIR, f"export_{tarih}.txt")
        with open(src, "r", encoding="utf-8") as f_in:
            with open(dst, "w", encoding="utf-8") as f_out:
                f_out.write("KIZIL Asistan Konuşma Dışa Aktarımı\n")
                f_out.write(f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f_out.write("-" * 40 + "\n")
                f_out.write(f_in.read())
        print(f"KIZIL: Konuşma günlüğü dışa aktarıldı: {dst}")

    # ---------- model değiştirme ----------

    def _change_model(self, girdi):
        yeni = girdi[6:].strip()
        if not yeni:
            print("KIZIL: Örnek: model phi3:mini")
            return
        self.router.model = yeni
        self.config.set("LLM_MODEL", yeni)
        print(f"KIZIL: Model '{yeni}' olarak değiştirildi.")

    # ---------- dinamik ayar ----------

    def _config_cmd(self, girdi):
        parcalar = girdi.split(maxsplit=2)
        if len(parcalar) == 1:
            print("KIZIL: Mevcut ayarlar:")
            for k, v in self.config._data.items():
                print(f"  {k} = {v}")
        elif len(parcalar) == 2:
            anahtar = parcalar[1].upper()
            if anahtar == "SIFIRLA":
                self.config._data = self.config._defaults()
                self.config.save()
                self.router.model = self.config.LLM_MODEL
                self.memory.context.clear()
                print("KIZIL: Tüm ayarlar varsayılana döndürüldü.")
                return
            try:
                deger = getattr(self.config, anahtar)
                print(f"KIZIL: {anahtar} = {deger}")
            except AttributeError:
                print(f"KIZIL: '{anahtar}' diye bir ayar bulunamadı.")
        else:
            anahtar = parcalar[1].upper()
            deger = parcalar[2]
            try:
                getattr(self.config, anahtar)
                self.config.set(anahtar, deger)
                if anahtar == "LLM_MODEL":
                    self.router.model = deger
                print(f"KIZIL: {anahtar} = {deger} olarak güncellendi.")
            except AttributeError:
                print(f"KIZIL: '{anahtar}' diye bir ayar bulunamadı.")

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
            print("KIZIL: LLM cagrisi sirasinda hata olustu.")
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
