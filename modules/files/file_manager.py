import os
import shutil
import tempfile
import time
from modules.tools.tool_manager import ToolManager
from modules.tools.path_utils import safe_path

PROJE_KOKU = os.path.realpath(os.getcwd())
KRITIK_DIZINLER = {"core", "modules", "storage"}
KRITIK_DOSYA_YOLLARI = {
    os.path.join(PROJE_KOKU, f)
    for f in ["main.py", "requirements.txt", ".env", ".gitignore", "README.md"]
}
MAX_DOSYA_BOYUTU_DOSYASI = 5000


def _safe_relpath(safe: str) -> str:
    try:
        return os.path.relpath(safe, PROJE_KOKU)
    except ValueError:
        return safe


class FileManager:
    """Temel dosya işlemleri için yardımcı sınıf (güvenlikli)."""

    @staticmethod
    def read_file(path):
        safe = safe_path(path)
        if not os.path.exists(safe):
            raise FileNotFoundError(f"Dosya bulunamadı: {_safe_relpath(safe)}")
        try:
            size = os.path.getsize(safe)
        except OSError:
            raise ValueError("Dosya boyutu okunamadı.")
        if size > 1_000_000:
            raise ValueError("Dosya çok büyük (1 MB sınırı).")
        chunks = []
        with open(safe, "r", encoding="utf-8") as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                chunks.append(chunk)
        return "".join(chunks)

    @staticmethod
    def write_file(path, content, overwrite=False):
        safe = safe_path(path)
        os.makedirs(os.path.dirname(safe) or ".", exist_ok=True)
        if not overwrite and os.path.exists(safe):
            raise FileExistsError(f"Dosya zaten mevcut, üzerine yazılmadı: {_safe_relpath(safe)}")
        tmp_fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(safe) or ".")
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                f.write(content)
            os.replace(tmp_path, safe)
        except Exception:
            # finally bloğu ile geçici dosyayı garantili temizle
            raise
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

    @staticmethod
    def list_files(directory, extension=None):
        safe_dir = safe_path(directory)
        if not os.path.exists(safe_dir):
            raise FileNotFoundError(f"Dizin bulunamadı: {_safe_relpath(safe_dir)}")
        files = []
        for e in os.listdir(safe_dir):
            full = os.path.join(safe_dir, e)
            try:
                if os.path.isfile(full) and (extension is None or e.endswith(extension)):
                    files.append(e)
            except (OSError, PermissionError):
                continue
        return files


# ---------- Araç fonksiyonları ----------

def _kendini_koruma(safe: str) -> str | None:
    safe = os.path.realpath(safe)
    if not safe.startswith(PROJE_KOKU + os.sep) and safe != PROJE_KOKU:
        return None
    if safe == PROJE_KOKU:
        return "Güvenlik: Proje ana dizini silinemez."
    rel = os.path.relpath(safe, PROJE_KOKU)
    if rel == ".":
        return "Güvenlik: Proje ana dizini silinemez."
    top_dir = rel.split(os.sep)[0]
    if top_dir in KRITIK_DIZINLER:
        return f"Güvenlik: Kritik dizin silinemez: {top_dir}"
    if safe in KRITIK_DOSYA_YOLLARI:
        return f"Güvenlik: Kritik dosya silinemez: {os.path.basename(safe)}"
    if os.path.isdir(safe):
        for kritik in KRITIK_DOSYA_YOLLARI:
            if os.path.commonpath([safe, kritik]) == safe:
                return f"Güvenlik: Bu dizin kritik dosya içeriyor ({os.path.basename(kritik)}), silinemez."
    return None


def _dosya_sil(dosya: str) -> str:
    try:
        safe = safe_path(dosya)
    except ValueError as e:
        return f"Güvenlik: {e}"
    koruma = _kendini_koruma(safe)
    if koruma:
        return koruma
    if not os.path.exists(safe):
        return f"Bulunamadı: {_safe_relpath(safe)}"
    # Atomik tip kontrolü: os.lstat ile yarış durumu önlenir
    try:
        st = os.lstat(safe)
    except OSError:
        return "Dosya durumu okunamadı."
    try:
        import stat
        if stat.S_ISLNK(st.st_mode):
            os.unlink(safe)
            return f"Silindi (symlink): {_safe_relpath(safe)}"
        if stat.S_ISDIR(st.st_mode):
            shutil.rmtree(safe)
        else:
            os.remove(safe)
        return f"Silindi: {_safe_relpath(safe)}"
    except Exception as e:
        return f"Silme hatası: {e}"


def _dosya_ara(dizin: str, isim: str) -> str:
    if len(isim.strip()) < 2:
        return "En az 2 karakterlik bir arama yapmalısınız."
    try:
        safe_dir = safe_path(dizin)
    except ValueError as e:
        return f"Güvenlik: {e}"
    if not os.path.isdir(safe_dir):
        return f"Dizin bulunamadı: {_safe_relpath(safe_dir)}"
    bulunan = []
    max_depth = 10
    max_dirs = 5000
    dir_count = 0
    base_depth = safe_dir.count(os.sep)
    for root, dirs, files in os.walk(safe_dir, followlinks=False):
        # Derinlik kontrolünü en başta yap, gereksiz derinlere inme
        depth = root.count(os.sep) - base_depth
        if depth > max_depth:
            dirs[:] = []
            continue
        dir_count += 1
        if dir_count > max_dirs:
            break
        for f in files:
            if isim.lower() in f.lower():
                bulunan.append(os.path.join(root, f))
                if len(bulunan) >= 20:
                    return "\n".join(bulunan)
    if not bulunan:
        return f"'{isim}' ile eşleşen dosya bulunamadı."
    return "\n".join(bulunan)


def _gecici_temizle() -> str:
    tmp = tempfile.gettempdir()
    sayi = 0
    hatali = 0
    su_an = time.time()
    esik = su_an - 300

    def _onerror(func, path, exc_info):
        nonlocal hatali
        hatali += 1

    try:
        for item in os.listdir(tmp):
            if not item.startswith("kizil_"):
                continue
            item_path = os.path.join(tmp, item)
            try:
                mtime = os.path.getmtime(item_path)
            except OSError:
                continue
            if mtime > esik:
                continue
            try:
                if os.path.islink(item_path):
                    os.unlink(item_path)
                    sayi += 1
                elif os.path.isfile(item_path):
                    os.remove(item_path)
                    sayi += 1
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path, onerror=_onerror)
                    if not os.path.exists(item_path):
                        sayi += 1
            except OSError:
                hatali += 1
        mesaj = f"{sayi} geçici dosya/klasör temizlendi (sadece 'kizil_' ön ekli, 5dk'dan eski)."
        if hatali > 0:
            mesaj += f" {hatali} öğe silinemedi."
        return mesaj
    except Exception as e:
        return f"Geçici temizlik hatası: {e}"


def _dosya_boyutu(dosya: str) -> str:
    try:
        safe = safe_path(dosya)
    except ValueError as e:
        return f"Güvenlik: {e}"
    if not os.path.exists(safe):
        return f"Bulunamadı: {_safe_relpath(safe)}"
    hatali = 0
    try:
        if os.path.isdir(safe):
            total = 0
            dosya_sayaci = 0
            done = False
            for root, _, files in os.walk(safe, followlinks=False):
                for f in files:
                    if dosya_sayaci >= MAX_DOSYA_BOYUTU_DOSYASI:
                        done = True
                        break
                    fp = os.path.join(root, f)
                    try:
                        total += os.path.getsize(fp)
                        dosya_sayaci += 1
                    except OSError:
                        hatali += 1
                if done:
                    break
            sonuc = f"'{_safe_relpath(safe)}' boyutu: {total / (1024**2):.1f} MB"
            if done:
                sonuc += f" (ilk {MAX_DOSYA_BOYUTU_DOSYASI} dosya üzerinden)"
            if hatali > 0:
                sonuc += f" (uyarı: {hatali} dosya okunamadı)"
            return sonuc
        else:
            size = os.path.getsize(safe)
            if size < 1024**2:
                return f"'{_safe_relpath(safe)}' boyutu: {size / 1024:.1f} KB"
            return f"'{_safe_relpath(safe)}' boyutu: {size / (1024**2):.1f} MB"
    except Exception as e:
        return f"Boyut alınamadı: {e}"


def _uzanti_listele(dizin: str, uzanti: str) -> str:
    if not uzanti.startswith("."):
        uzanti = f".{uzanti}"
    try:
        safe_dir = safe_path(dizin)
    except ValueError as e:
        return f"Güvenlik: {e}"
    if not os.path.isdir(safe_dir):
        return f"Dizin bulunamadı: {_safe_relpath(safe_dir)}"
    try:
        tum_dosyalar = []
        for f in os.listdir(safe_dir):
            full = os.path.join(safe_dir, f)
            try:
                if os.path.isfile(full) and f.endswith(uzanti):
                    tum_dosyalar.append(f)
            except (OSError, PermissionError):
                continue
        tum_dosyalar.sort()
        limit = 30
        secilenler = tum_dosyalar[:limit]
        if not secilenler:
            return f"'{_safe_relpath(safe_dir)}' içinde '{uzanti}' uzantılı dosya bulunamadı."
        sonuc = "\n".join(secilenler)
        if len(tum_dosyalar) > limit:
            sonuc += f"\n... ve {len(tum_dosyalar) - limit} dosya daha"
        return sonuc
    except Exception as e:
        return f"Listeleme hatası: {e}"


def register_file_tools(manager: ToolManager) -> None:
    manager.register(
        name="dosya_sil",
        description="Bir dosyayı veya klasörü siler.",
        parameters={"dosya": "Silinecek dosya/klasör yolu"},
        func=_dosya_sil,
    )
    manager.register(
        name="dosya_ara",
        description="Belirtilen dizinde dosya adı arar (en fazla 10 derinlik, 5000 klasör).",
        parameters={"dizin": "Aranacak dizin", "isim": "Dosya adı veya kısmı (en az 2 karakter)"},
        func=_dosya_ara,
    )
    manager.register(
        name="gecici_temizle",
        description="Sadece 'kizil_' ön ekli ve 5 dakikadan eski geçici dosyaları temizler.",
        parameters={},
        func=_gecici_temizle,
    )
    manager.register(
        name="dosya_boyutu",
        description="Dosya veya klasörün boyutunu gösterir (en fazla 5000 dosya taranır).",
        parameters={"dosya": "Dosya/klasör yolu"},
        func=_dosya_boyutu,
    )
    manager.register(
        name="uzanti_listele",
        description="Belirtilen uzantıdaki dosyaları listeler.",
        parameters={"dizin": "Dizin yolu", "uzanti": "Dosya uzantısı (örn: py, txt)"},
        func=_uzanti_listele,
    )
