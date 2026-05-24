"""Yerel bilgisayar otomasyon araçları."""
import os
import shutil
import subprocess
import platform
from modules.tools.tool_manager import ToolManager
from modules.tools.path_utils import safe_path

_IS_WIN = platform.system() == "Windows"
_IS_MAC = platform.system() == "Darwin"

SAFE_APPS = {
    "notepad": ["notepad.exe"] if _IS_WIN else (["open", "-a", "TextEdit"] if _IS_MAC else ["gedit"]),
    "gedit": ["gedit"],
    "calc": ["calc.exe"] if _IS_WIN else (["open", "-a", "Calculator"] if _IS_MAC else ["gnome-calculator"]),
    "calculator": ["gnome-calculator"],
    "browser": ["firefox"] if not _IS_MAC else ["open", "-a", "Firefox"],
    "firefox": ["firefox"] if not _IS_MAC else ["open", "-a", "Firefox"],
    "chrome": ["google-chrome"] if not _IS_MAC else ["open", "-a", "Google Chrome"],
    "terminal": ["gnome-terminal"] if not _IS_MAC else ["open", "-a", "Terminal"],
    "finder": ["open"] if _IS_MAC else None,
    "explorer": ["explorer.exe"] if _IS_WIN else None,
}

# psutil cpu_percent sayaç körlüğünü kır
try:
    import psutil
    psutil.cpu_percent(interval=None)
except Exception:
    pass


def _mac_app_var(app_name: str) -> bool:
    for base in ["/Applications", os.path.expanduser("~/Applications")]:
        app_path = os.path.join(base, f"{app_name}.app")
        if os.path.isdir(app_path):
            return True
    return False


def _safe_env() -> dict:
    env = {"PATH": os.environ.get("PATH", "")}
    if _IS_WIN:
        for key in ["SYSTEMROOT", "WINDIR", "USERPROFILE",
                    "SYSTEMDRIVE", "PROGRAMFILES", "PROGRAMFILES(X86)",
                    "LOCALAPPDATA"]:
            val = os.environ.get(key, "")
            if val:
                env[key] = val
    else:
        for key in ["HOME", "DISPLAY", "XAUTHORITY", "DBUS_SESSION_BUS_ADDRESS"]:
            val = os.environ.get(key, "")
            if val:
                env[key] = val
    return env


def _headless_guvenli() -> bool:
    """Grafik arayüz olup olmadığını kontrol eder."""
    if _IS_WIN:
        return True  # Windows'ta genelde grafik arayüz vardır
    # POSIX: DISPLAY değişkeni yoksa headless sunucudur
    return bool(os.environ.get("DISPLAY"))


def _klasor_olustur(dizin: str) -> str:
    try:
        safe = safe_path(dizin)
    except ValueError as e:
        return f"Güvenlik: {e}"
    try:
        os.makedirs(safe, exist_ok=True)
        return f"Klasör oluşturuldu: {safe}"
    except OSError as e:
        return f"Klasör oluşturulamadı (disk dolu veya izin hatası): {e}"
    except Exception as e:
        return f"Klasör oluşturulamadı: {e}"


def _dosya_tasi(kaynak: str, hedef: str) -> str:
    try:
        safe_src = safe_path(kaynak)
        safe_dst = safe_path(hedef)
    except ValueError as e:
        return f"Güvenlik: {e}"
    if not os.path.exists(safe_src):
        return f"Kaynak bulunamadı: {safe_src}"
    if os.path.realpath(safe_src) == os.path.realpath(safe_dst):
        return "Kaynak ve hedef aynı olamaz."
    if os.path.isdir(safe_src):
        try:
            if os.path.commonpath([os.path.realpath(safe_src), os.path.realpath(safe_dst)]) == os.path.realpath(safe_src):
                return "Hedef, kaynak dizinin içinde olamaz."
        except ValueError:
            pass
    dst_dir = os.path.dirname(safe_dst)
    if dst_dir:
        try:
            os.makedirs(dst_dir, exist_ok=True)
        except OSError as e:
            return f"Hedef dizin oluşturulamadı (disk dolu veya izin hatası): {e}"
    # Atomik taşıma: kontrol + işlem yerine doğrudan dene
    try:
        shutil.move(safe_src, safe_dst)
        return f"Taşındı: {safe_src} → {safe_dst}"
    except FileExistsError:
        return f"Hedef zaten mevcut, taşınmadı: {safe_dst}"
    except OSError as e:
        return f"Taşıma hatası (disk dolu veya izin hatası): {e}"
    except Exception as e:
        return f"Taşıma hatası: {e}"


def _dosya_kopyala(kaynak: str, hedef: str) -> str:
    try:
        safe_src = safe_path(kaynak)
        safe_dst = safe_path(hedef)
    except ValueError as e:
        return f"Güvenlik: {e}"
    if not os.path.exists(safe_src):
        return f"Kaynak bulunamadı: {safe_src}"
    if os.path.realpath(safe_src) == os.path.realpath(safe_dst):
        return "Kaynak ve hedef aynı olamaz."
    if os.path.isdir(safe_src):
        try:
            if os.path.commonpath([os.path.realpath(safe_src), os.path.realpath(safe_dst)]) == os.path.realpath(safe_src):
                return "Hedef, kaynak dizinin içinde olamaz."
        except ValueError:
            pass
    dst_parent = os.path.dirname(safe_dst)
    if dst_parent:
        try:
            os.makedirs(dst_parent, exist_ok=True)
        except OSError as e:
            return f"Hedef dizin oluşturulamadı (disk dolu veya izin hatası): {e}"
    # Atomik kopyalama: doğrudan dene
    try:
        if os.path.isdir(safe_src):
            shutil.copytree(safe_src, safe_dst, dirs_exist_ok=False)
        else:
            shutil.copy2(safe_src, safe_dst)
        return f"Kopyalandı: {safe_src} → {safe_dst}"
    except FileExistsError:
        return f"Hedef zaten mevcut, kopyalanmadı: {safe_dst}"
    except OSError as e:
        return f"Kopyalama hatası (disk dolu veya izin hatası): {e}"
    except Exception as e:
        return f"Kopyalama hatası: {e}"


def _sistem_bilgisi() -> str:
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=None)
        if cpu == 0.0:
            import time
            time.sleep(0.1)
            cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory()
        if _IS_WIN:
            root_dir = os.path.splitdrive(os.getcwd())[0] + "\\"
        else:
            root_dir = "/"
        disk = psutil.disk_usage(root_dir)
        return (
            f"İşletim Sistemi: {platform.system()} {platform.release()}\n"
            f"CPU Kullanımı: %{cpu}\n"
            f"RAM: %{ram.percent} (kullanılan: {ram.used // (1024**2)} MB / {ram.total // (1024**2)} MB)\n"
            f"Disk ({root_dir}): %{disk.percent} (boş: {disk.free // (1024**3)} GB / {disk.total // (1024**3)} GB)"
        )
    except ImportError:
        return (
            f"İşletim Sistemi: {platform.system()} {platform.release()}\n"
            f"psutil yüklü değil, detaylı bilgi alınamadı."
        )
    except Exception as e:
        return f"Sistem bilgisi alınamadı: {e}"


def _uygulama_baslat(ad: str) -> str:
    ad = ad.lower().strip()
    if ad not in SAFE_APPS:
        return f"Güvenlik: '{ad}' beyaz listede yok. İzinli uygulamalar: {', '.join(SAFE_APPS.keys())}"
    cmd_list = SAFE_APPS[ad]
    if cmd_list is None:
        return f"'{ad}' bu işletim sisteminde desteklenmiyor."

    exe = cmd_list[0]
    if _IS_MAC and exe == "open" and len(cmd_list) >= 3 and cmd_list[1] == "-a":
        app_name = cmd_list[2]
        if not _mac_app_var(app_name):
            return f"'{ad}' uygulaması macOS'te bulunamadı (aranan: {app_name})."
    else:
        if shutil.which(exe) is None:
            return f"'{ad}' uygulaması sisteminizde bulunamadı (aranan: {exe})."

    # Headless kontrol: grafik arayüz olmayan sunucularda başlatma
    if not _headless_guvenli() and ad in ("browser", "firefox", "chrome", "terminal", "gedit", "calc", "calculator"):
        return f"'{ad}' grafik arayüz gerektirir, bu sistem headless (sunucu) olabilir."

    try:
        subprocess.Popen(cmd_list, env=_safe_env(), shell=False)
        return f"Uygulama başlatıldı: {ad}"
    except OSError as e:
        return f"Uygulama başlatılamadı (sistem hatası): {e}"
    except Exception as e:
        return f"Uygulama başlatılamadı: {e}"


def register_automation_tools(manager: ToolManager) -> None:
    manager.register(
        name="klasor_olustur",
        description="Yeni bir klasör oluşturur.",
        parameters={"dizin": "Oluşturulacak klasör yolu"},
        func=_klasor_olustur,
    )
    manager.register(
        name="dosya_tasi",
        description="Bir dosyayı başka bir konuma taşır.",
        parameters={"kaynak": "Taşınacak dosyanın yolu", "hedef": "Hedef yol"},
        func=_dosya_tasi,
    )
    manager.register(
        name="dosya_kopyala",
        description="Bir dosyayı veya klasörü kopyalar.",
        parameters={"kaynak": "Kaynak yol", "hedef": "Hedef yol"},
        func=_dosya_kopyala,
    )
    manager.register(
        name="sistem_bilgisi",
        description="CPU, RAM ve disk kullanım bilgilerini döner.",
        parameters={},
        func=_sistem_bilgisi,
    )
    manager.register(
        name="uygulama_baslat",
        description="Beyaz listedeki bir uygulamayı başlatır (headless sistemlerde grafik uygulamaları engeller).",
        parameters={"ad": "Uygulama adı (notepad, calc, browser, terminal vb.)"},
        func=_uygulama_baslat,
    )
