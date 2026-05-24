"""KIZIL Asistan için yerleşik araç tanımları."""
import os
import re
import shutil
import subprocess
import tempfile
import platform
from datetime import datetime, timezone
from modules.tools.tool_manager import ToolManager
from modules.tools.path_utils import safe_path

_IS_WIN = platform.system() == "Windows"
PROJE_KOKU = os.path.realpath(os.getcwd())

_UNIX_COMMANDS = ["ls", "pwd", "whoami", "date", "uptime", "df", "free", "ps"]
_WIN_COMMANDS = ["whoami", "date", "dir", "tasklist"]

SAFE_COMMANDS = []
for cmd in (_WIN_COMMANDS if _IS_WIN else _UNIX_COMMANDS):
    if _IS_WIN and cmd == "dir":
        SAFE_COMMANDS.append(cmd)
    elif shutil.which(cmd):
        SAFE_COMMANDS.append(cmd)

MAX_FILE_READ_BYTES = 500_000
MAX_COMMAND_OUTPUT = 5000
MAX_DIR_ENTRIES = 1000  # listelemede belleğe alınacak maksimum öğe


def _safe_env() -> dict:
    env = {"PATH": os.environ.get("PATH", "")}
    if _IS_WIN:
        for key in ["SYSTEMROOT", "WINDIR", "USERPROFILE"]:
            val = os.environ.get(key, "")
            if val:
                env[key] = val
    return env


def _safe_command(cmd: str) -> str:
    parts = cmd.strip().split()
    if not parts:
        return "Komut belirtilmedi."
    if len(parts) > 1:
        return "Güvenlik: Komut argüman alamaz, sadece komut adı girin."
    base = parts[0]
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", base):
        return f"Güvenlik: Geçersiz komut adı: {base}"
    if base not in SAFE_COMMANDS:
        return f"Güvenlik: '{base}' izinli değil. İzinli komutlar: {', '.join(SAFE_COMMANDS)}"
    if _IS_WIN and base == "dir":
        cmd_path = "dir"
    else:
        cmd_path = shutil.which(base)
        if cmd_path is None:
            return f"Komut bulunamadı: {base}"
    try:
        if _IS_WIN and base == "dir":
            result = subprocess.run(
                ["cmd", "/c", "dir"], capture_output=True, text=True, timeout=5,
                cwd=PROJE_KOKU, env=_safe_env(), shell=False
            )
        else:
            result = subprocess.run(
                [cmd_path], capture_output=True, text=True, timeout=5,
                cwd=PROJE_KOKU, env=_safe_env(), shell=False
            )
        out = result.stdout or ""
        err = result.stderr or ""
        if len(out) > MAX_COMMAND_OUTPUT:
            out = out[:MAX_COMMAND_OUTPUT] + f"\n... [stdout kırpıldı: {len(out) - MAX_COMMAND_OUTPUT} karakter]"
        if len(err) > MAX_COMMAND_OUTPUT:
            err = err[:MAX_COMMAND_OUTPUT] + f"\n... [stderr kırpıldı: {len(err) - MAX_COMMAND_OUTPUT} karakter]"
        output = out + err
        return output if output.strip() else "(komut çıktı vermedi)"
    except subprocess.TimeoutExpired:
        return f"Komut zaman aşımına uğradı (5 saniye): {base}"
    except FileNotFoundError:
        return f"Komut bulunamadı: {base}"
    except Exception as e:
        return f"Komut hatası: {e}"


def _dosya_oku(dosya_yolu: str) -> str:
    try:
        safe = safe_path(dosya_yolu)
    except ValueError as e:
        return f"Güvenlik: {e}"
    if not os.path.isfile(safe):
        return f"Dosya bulunamadı: {safe}"
    try:
        size = os.path.getsize(safe)
    except OSError:
        return "Dosya boyutu okunamadı, güvenlik nedeniyle okunmadı."
    if size > MAX_FILE_READ_BYTES:
        return f"Dosya çok büyük ({size / 1024:.0f} KB), okunmadı. Sınır: {MAX_FILE_READ_BYTES // 1024} KB."
    try:
        with open(safe, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except UnicodeDecodeError:
        return "Bu dosya metin formatında değil, okunamadı."
    except FileNotFoundError:
        return "Dosya işlem sırasında silindi veya taşındı."
    except PermissionError:
        return "Dosya okuma izni yok."
    except Exception as e:
        return f"Dosya okuma hatası: {e}"


def _dosya_yaz(dosya_yolu: str, icerik: str) -> str:
    try:
        safe = safe_path(dosya_yolu)
    except ValueError as e:
        return f"Güvenlik: {e}"
    if os.path.exists(safe):
        return f"Dosya zaten mevcut, üzerine yazılmadı: {safe}"
    try:
        os.makedirs(os.path.dirname(safe) or ".", exist_ok=True)
    except OSError as e:
        return f"Dizin oluşturulamadı: {e}"
    tmp_fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(safe) or ".")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write(icerik)
        os.replace(tmp_path, safe)
    except FileExistsError:
        return f"Dosya zaten mevcut, üzerine yazılmadı: {safe}"
    except PermissionError:
        return "Dosya yazma izni yok."
    except Exception as e:
        return f"Dosya yazma hatası: {e}"
    finally:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
    return f"{safe} yazıldı."


def _dosya_listele(dizin: str = ".") -> str:
    try:
        safe = safe_path(dizin)
    except ValueError as e:
        return f"Güvenlik: {e}"
    if not os.path.isdir(safe):
        return f"Dizin bulunamadı: {safe}"
    entries = []
    try:
        with os.scandir(safe) as it:
            for entry in it:
                name = str(entry.name)
                try:
                    if entry.is_dir():
                        entries.append((name, "[D]"))
                    elif entry.is_file():
                        entries.append((name, "[F]"))
                    else:
                        entries.append((name, "[?]"))
                except OSError:
                    entries.append((name, "[?] erişilemez"))
                # Bellek koruması: maksimum MAX_DIR_ENTRIES öğe
                if len(entries) >= MAX_DIR_ENTRIES:
                    break
    except PermissionError:
        return "Dizin listeleme izni yok."
    entries.sort(key=lambda x: x[0].lower())
    secilenler = entries[:50]
    out = [f"{prefix} {name}" for name, prefix in secilenler]
    if not out:
        return "Dizin boş veya erişilemez."
    if len(entries) > 50:
        out.append(f"... ve {len(entries) - 50} öğe daha")
    return "\n".join(out)


def register_builtin_tools(manager: ToolManager) -> None:
    manager.register(
        name="dosya_oku",
        description="Bir dosyanın içeriğini okur (en fazla 500 KB).",
        parameters={"dosya_yolu": "Okunacak dosyanın yolu"},
        func=_dosya_oku,
    )
    manager.register(
        name="dosya_yaz",
        description="Bir dosyaya atomik yazar (mevcutsa üzerine yazmaz). Klasör yoksa oluşturur.",
        parameters={"dosya_yolu": "Yazılacak dosya", "icerik": "Yazılacak metin"},
        func=_dosya_yaz,
    )
    manager.register(
        name="dosya_listele",
        description="Belirtilen dizindeki dosya ve klasörleri listeler ([D]=dizin, [F]=dosya, [?]=erişilemez).",
        parameters={"dizin": "Listelenecek dizin (opsiyonel, varsayılan: bulunulan dizin)"},
        func=_dosya_listele,
    )
    manager.register(
        name="zaman",
        description="Anlık UTC tarih ve saat bilgisini döner.",
        parameters={},
        func=lambda: datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M:%S UTC"),
    )
    manager.register(
        name="komut_calistir",
        description="Güvenli sistem komutu çalıştırır (argümansız, sadece harf/rakam/tire).",
        parameters={"komut": "Çalıştırılacak komut adı"},
        func=lambda komut: _safe_command(komut),
    )
