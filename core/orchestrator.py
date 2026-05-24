import os
from datetime import datetime
from modules.chat.chat_module import ChatModule
from core.llm_router import LLMRouter
from modules.tasks.task_manager import TaskManager
from core.memory_manager import MemoryManager
from modules.session.session_manager import SessionManager
from modules.tools.tool_manager import ToolManager
from modules.tools.builtin_tools import register_builtin_tools
from modules.browser.browser_tools import register_browser_tools
from modules.automation.automation_tools import register_automation_tools
from modules.files.file_manager import register_file_tools
from modules.profile import ProfileManager
from modules.plugins.plugin_loader import PluginLoader
from utils.logger import Logger
from utils.config import Config

AUTO_SUMMARIZE_THRESHOLD = 20


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
        self.profile = ProfileManager()

        self.chat.set_logger(self.logger)
        self.chat.set_metrics_file(os.path.join(self.config.STORAGE_DIR, "metrics.json"))
        self.memory.set_logger(self.logger)

        self.tool_manager = ToolManager()
        register_builtin_tools(self.tool_manager)
        register_browser_tools(self.tool_manager)
        register_automation_tools(self.tool_manager)
        register_file_tools(self.tool_manager)
        self._register_task_tools()
        self.chat.set_tool_manager(self.tool_manager)
        self.chat.set_profile_prompt(self.profile.get_prompt())

        # Undo mekanizması
        self._last_action: dict | None = None  # {"type": "task_add"|"task_del"|"task_done", "data": ...}

        self.command_map = {
            "özetle": self._summary,
            "sıfırla": self._reset_context,
            "hatalar": self._show_errors,
            "oturumlar": self._show_sessions,
            "dışa aktar": self._export_conversation,
            "görevler": self._task_list,
            "görev listesi": self._task_list,
            "profil": lambda: self._profile_cmd("profil"),
            "ayar": lambda: self._config_cmd("ayar"),
            "durum": self._show_status,
            "karaliste": self._show_blacklist,
            "geri al": self._undo,
        }

        self.param_commands = [
            ("hatırla ", self._remember),
            ("görev ekle ", self._task_add),
            ("görev sil ", self._task_del),
            ("görev tamam ", self._task_done),
            ("görev zincirle ", self._task_chain),
            ("model ", self._change_model),
            ("profil ", self._profile_cmd),
            ("ayar ", self._config_cmd),
            ("karaliste temizle", lambda _: self._clear_blacklist()),
        ]

        self.plugin_loader = PluginLoader(self)
        yuklenenler = self.plugin_loader.load_all()
        if yuklenenler:
            self.logger.info(f"Pluginler yüklendi: {', '.join(yuklenenler)}")

        self._mesaj_sayaci = 0
        self.running = False

    def _register_task_tools(self) -> None:
        self.tool_manager.register(
            name="gorev_ekle",
            description="Yeni görev ekler.",
            parameters={"aciklama": "Görev açıklaması"},
            func=lambda aciklama: self._add_task_tool(aciklama),
        )
        self.tool_manager.register(
            name="gorev_listele",
            description="Tüm görevleri listeler.",
            parameters={},
            func=lambda: self._list_tasks_tool(),
        )

    def _add_task_tool(self, aciklama: str) -> str:
        try:
            t = self.task_mgr.add_task(aciklama)
            return f"Görev eklendi: [{t['id']}] {t['desc']}"
        except Exception as e:
            return f"Görev eklenemedi: {e}"

    def _list_tasks_tool(self) -> str:
        try:
            tasks = self.task_mgr.list_tasks()
            if not tasks:
                return "Henüz görev yok."
            out = []
            for t in tasks:
                durum = "✓" if t.get("done") else "☐"
                zincir = f" ⛓→{t['depends_on']}" if t.get("depends_on") else ""
                out.append(f"{durum} [{t['id']}]{zincir} {t['desc']}")
            return "\n".join(out)
        except Exception as e:
            return f"Görevler listelenemedi: {e}"

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
        self.logger.info(f"Kullanıcı girdisi: {girdi}")
        try:
            komut = girdi.lower().strip()

            if komut in ("çık", "exit", "quit", "q"):
                self.stop()
                return
            if komut in ("yardım", "yardim", "help", "h"):
                self._help()
                return

            if komut in self.command_map:
                self.command_map[komut]()
                return

            for prefix, handler in self.param_commands:
                if komut.startswith(prefix):
                    handler(girdi)
                    return

            self._chat(girdi)

        except Exception as e:
            self.logger.error(f"İşlem hatası: {e}", exc_info=True)
            print("KIZIL: Bir hata oluştu. Lütfen tekrar dene.")

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
görev zincirle <id1> <id2>    → 2. görevi 1. göreve bağlar
geri al                       → son görev işlemini geri al
model <model_adi>             → LLM modelini değiştir
ayar                          → tüm ayarları listele
ayar <anahtar>                → anahtarın değerini göster
ayar <anahtar> <değer>        → anahtarı güncelle
ayar sıfırla                  → tüm ayarları varsayılana döndür
hatalar                       → son hata loglarını göster
oturumlar                     → geçmiş oturumları listele
dışa aktar                    → konuşma günlüğünü dışa aktar
profil                        → profil bilgilerini göster
profil <anahtar> <değer>      → profil alanını güncelle (ad, tercih, not)
durum                         → asistan performans raporu
karaliste                     → devre dışı bırakılan araçları listele
karaliste temizle             → kara listeyi ve panik modunu sıfırla
        """.strip())

    def _profile_cmd(self, girdi):
        parcalar = girdi.split(maxsplit=3)
        if len(parcalar) == 1:
            veri = self.profile.get_all()
            print("KIZIL: Kullanıcı Profili")
            for k, v in veri.items():
                if v:
                    print(f"  {k}: {v}")
                else:
                    print(f"  {k}: (boş)")
        elif len(parcalar) == 2:
            print("KIZIL: Kullanım: profil <anahtar> <değer>")
            print("  Örnek: profil ad Esat")
        elif len(parcalar) >= 3:
            anahtar = parcalar[1].lower()
            if anahtar == "ad":
                deger = parcalar[2]
                self.profile.set("ad", deger)
                print(f"KIZIL: İsmin '{deger}' olarak kaydedildi.")
            elif anahtar == "tercih":
                if len(parcalar) >= 4:
                    tercih_adi = parcalar[2]
                    tercih_deger = parcalar[3]
                    self.profile._data.setdefault("tercihler", {})
                    self.profile._data["tercihler"][tercih_adi] = tercih_deger
                    self.profile.save()
                    print(f"KIZIL: Tercih '{tercih_adi}' = '{tercih_deger}' kaydedildi.")
                else:
                    print("KIZIL: Kullanım: profil tercih <ad> <değer>")
                    print("  Örnek: profil tercih renk kırmızı")
            elif anahtar == "not":
                deger = parcalar[2]
                self.profile.set("notlar", deger)
                print("KIZIL: Not kaydedildi.")
            elif anahtar == "model":
                deger = parcalar[2]
                self.profile.set("model", deger)
                print(f"KIZIL: Tercih ettiğin model '{deger}' olarak kaydedildi.")
            else:
                deger = parcalar[2]
                self.profile.set(anahtar, deger)
                print(f"KIZIL: '{anahtar}' = '{deger}' olarak kaydedildi.")
            self.chat.set_profile_prompt(self.profile.get_prompt())

    def _reset_context(self):
        self.memory.context.clear()
        self._mesaj_sayaci = 0
        print("KIZIL: Konuşma geçmişi temizlendi.")

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

    def _show_sessions(self):
        sessions = self.session.list_sessions()
        if not sessions:
            print("KIZIL: Henüz oturum kaydı yok.")
            return
        print("KIZIL: Geçmiş oturumlar:")
        for s in sessions:
            durum = "✅" if s.get("end") else "🔄"
            print(f"  {durum} {s['id']} | {s['start']} → {s.get('end', 'devam ediyor')}")

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

    def _change_model(self, girdi):
        yeni = girdi.split(maxsplit=1)[1].strip() if " " in girdi else ""
        if not yeni:
            print("KIZIL: Örnek: model phi3:mini")
            return
        self.router.model = yeni
        self.config.set("LLM_MODEL", yeni)
        self.chat.set_profile_prompt(self.profile.get_prompt())
        print(f"KIZIL: Model '{yeni}' olarak değiştirildi.")

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
                self.chat.set_profile_prompt(self.profile.get_prompt())
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

    def _safe_llm(self, func, *args):
        try:
            return func(*args)
        except ConnectionError:
            print("KIZIL: LLM baglantisi kurulamadi.")
            print("  -> Ollama calisiyor mu? (http://localhost:11434)")
            print("  -> Model yuklu mu? 'ollama list' ile kontrol et.")
            return None
        except Exception as e:
            self.logger.error(f"LLM hatasi: {e}", exc_info=True)
            print("KIZIL: LLM cagrisi sirasinda hata olustu.")
            print(f"  -> Hata: {e}")
            return None

    def _chat(self, msg):
        def istek():
            ctx = self.memory.get_context()
            resp = self.chat.yanit_ver(msg, ctx)
            print("KIZIL:", resp)
            return resp

        resp = self._safe_llm(istek)
        if resp is not None:
            self.memory.save_conversation(msg, resp)
            self.memory.add_to_context("user", msg)
            self.memory.add_to_context("assistant", resp)
            self._mesaj_sayaci += 2
            if self._mesaj_sayaci >= AUTO_SUMMARIZE_THRESHOLD:
                self._summary()
                self._mesaj_sayaci = 0

    def _summary(self):
        def istek():
            f, s = self.memory.summarize_and_save(self.router.model, self.chat)
            if f:
                print(f"KIZIL: Özet kaydedildi: {f}")
                print("Özet:", s)
                self.profile.update_from_summary(s)
                self.chat.set_profile_prompt(self.profile.get_prompt())
            else:
                print("KIZIL:", s)
            return s

        self._safe_llm(istek)

    def _remember(self, girdi):
        q = girdi.split(maxsplit=1)[1].strip() if " " in girdi else ""
        if not q:
            print("KIZIL: Ne hakkında hatırlatma yapmamı istersin?")
            return

        def istek():
            a = self.memory.search_memory(q, self.chat)
            print("KIZIL:", a)
            return a

        resp = self._safe_llm(istek)
        if resp is not None:
            self.memory.save_conversation(girdi, resp)
            self.memory.add_to_context("user", girdi)
            self.memory.add_to_context("assistant", resp)

    def _task_add(self, girdi):
        parcalar = girdi.split(maxsplit=2)
        if len(parcalar) < 3:
            print("KIZIL: Örnek: görev ekle markete git")
            return
        desc = parcalar[2].strip()
        try:
            t = self.task_mgr.add_task(desc)
            self._last_action = {"type": "task_add", "id": t["id"]}
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
                zincir = ""
                if t.get("depends_on"):
                    zincir = f" ⛓→{t['depends_on']}"
                print(f"  {durum} [{t['id']}]{zincir} {t['desc']}")
        except Exception as e:
            self.logger.error(f"Görev listeleme hatası: {e}")
            print("KIZIL: Görevler listelenemedi.")

    def _task_del(self, girdi):
        parcalar = girdi.split(maxsplit=2)
        if len(parcalar) < 3:
            print("KIZIL: Örnek: görev sil <id>")
            return
        gid = parcalar[2].strip()
        try:
            ok = self.task_mgr.delete_task(gid)
            if ok:
                self._last_action = {"type": "task_del", "id": gid}
            print(f"KIZIL: Görev #{gid} silindi." if ok else f"KIZIL: Görev #{gid} bulunamadı.")
        except (ValueError, TypeError):
            print(f"KIZIL: Geçersiz görev ID: {gid}")
        except Exception as e:
            self.logger.error(f"Görev silme hatası: {e}")
            print("KIZIL: Görev silinirken hata oluştu.")

    def _task_done(self, girdi):
        parcalar = girdi.split(maxsplit=2)
        if len(parcalar) < 3:
            print("KIZIL: Örnek: görev tamam <id>")
            return
        gid = parcalar[2].strip()
        try:
            ok, mesaj = self.task_mgr.mark_done(gid)
            if ok and "tamamlandı" in mesaj:
                self._last_action = {"type": "task_done", "id": gid}
            print(f"KIZIL: {mesaj}")
            if ok and "tamamlandı" in mesaj:
                tasks = self.task_mgr.list_tasks()
                for t in tasks:
                    if t.get("depends_on") == gid and not t.get("done"):
                        print(f"  💡 '{t['desc']}' görevi [#{t['id']}] bu göreve bağlıydı. Tamamlamak ister misin?")
                        break
        except (ValueError, TypeError):
            print(f"KIZIL: Geçersiz görev ID: {gid}")
        except Exception as e:
            self.logger.error(f"Görev tamamlama hatası: {e}")
            print("KIZIL: Görev tamamlanırken hata oluştu.")

    def _task_chain(self, girdi):
        parcalar = girdi.split()
        if len(parcalar) < 4:
            print("KIZIL: Örnek: görev zincirle <id1> <id2>")
            return
        id1 = parcalar[2].strip()
        id2 = parcalar[3].strip()
        try:
            sonuc = self.task_mgr.chain_tasks(id1, id2)
            print(f"KIZIL: {sonuc}")
        except (ValueError, TypeError):
            print("KIZIL: Geçersiz görev ID'leri.")
        except Exception as e:
            self.logger.error(f"Görev zincirleme hatası: {e}")
            print("KIZIL: Görev zincirleme sırasında hata oluştu.")

    def _undo(self):
        if not self._last_action:
            print("KIZIL: Geri alınacak işlem yok.")
            return
        action = self._last_action
        try:
            if action["type"] == "task_add":
                ok = self.task_mgr.delete_task(action["id"])
                print(f"KIZIL: Görev #{action['id']} geri alındı (silindi)." if ok else "KIZIL: Geri alma başarısız.")
            elif action["type"] == "task_del":
                print("KIZIL: Görev silme geri alınamaz (veri kayboldu).")
            elif action["type"] == "task_done":
                # Tamamlanan görevi geri al (done=False yap)
                tasks = self.task_mgr.list_tasks()
                for t in tasks:
                    if t["id"] == action["id"]:
                        t["done"] = False
                        self.task_mgr._save(tasks)
                        print(f"KIZIL: Görev #{action['id']} tamamlandı işareti geri alındı.")
                        break
                else:
                    print("KIZIL: Görev bulunamadı, geri alınamadı.")
            self._last_action = None
        except Exception as e:
            print(f"KIZIL: Geri alma hatası: {e}")

    def _show_status(self):
        m = self.chat.get_metrics()
        blacklisted = self.chat.get_blacklisted_tools()
        panic = self.chat.is_panic_mode()
        prompt = (
            f"Asistan performans metrikleri:\n"
            f"Toplam araç çağrısı: {m['toplam_arac_cagrisi']}\n"
            f"Başarılı: {m['basarili_arac_cagrisi']}\n"
            f"Başarısız: {m['basarisiz_arac_cagrisi']}\n"
            f"Kırılan zincir: {m['kirilan_zincir']}\n"
        )
        if blacklisted:
            prompt += f"Devre dışı bırakılan araçlar: {', '.join(blacklisted)}\n"
        if panic:
            prompt += "Uyarı: Sistem panik modunda! Araç kullanımı durduruldu.\n"
        prompt += "\nBu metrikleri Türkçe, doğal bir dille özetle. Kısa ve net bir performans raporu ver."

        def istek():
            resp = self.chat.yanit_ver(prompt)
            print("KIZIL:", resp)
            return resp

        self._safe_llm(istek)

    def _show_blacklist(self):
        blacklisted = self.chat.get_blacklisted_tools()
        panic = self.chat.is_panic_mode()
        if panic:
            print("⚠️  KIZIL panik modunda! Araç kullanımı tamamen durduruldu.")
        if blacklisted:
            print(f"KIZIL: Devre dışı bırakılan araçlar: {', '.join(blacklisted)}")
        else:
            print("KIZIL: Şu anda kara listede araç yok.")
        print("  'karaliste temizle' yazarak sıfırlayabilirsiniz.")

    def _clear_blacklist(self):
        self.chat._blacklisted_tools.clear()
        self.chat._tool_fail_counts.clear()
        self.chat.reset_panic()
        print("KIZIL: Kara liste temizlendi, panik modu sıfırlandı. Tüm araçlar tekrar kullanılabilir.")

    def stop(self):
        self.chat.save_metrics()
        self.session.end_session()
        self.running = False
        self.logger.info("KIZIL Asistan kapatılıyor.")
        print("Görüşmek üzere!")
