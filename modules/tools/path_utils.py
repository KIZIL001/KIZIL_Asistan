"""Merkezi güvenli yol denetimi – tüm modüller için ortak."""
import os
import sys


def safe_path(path: str, base_dir: str | None = None, must_exist: bool = False) -> str:
    """
    Yolu mutlak yapar, sembolik bağları çözer, proje dizini dışına çıkmayı engeller.
    must_exist=True ise yolun fiziksel olarak var olması zorunludur.
    """
    if not path:
        raise ValueError("Yol boş olamaz.")

    # Gizli karakter temizliği: null byte ve boşluklar
    path = path.strip().replace("\x00", "")

    if os.path.islink(path):
        raise ValueError("Sembolik bağlara (symlink) izin verilmez.")

    resolved = os.path.realpath(os.path.abspath(path))

    parts = resolved.replace("\\", "/").split("/")
    if ".." in parts:
        raise ValueError("Yol '..' içeremez.")

    if base_dir is None:
        base_dir = os.getcwd()
    base_resolved = os.path.realpath(os.path.abspath(base_dir))

    # Windows/macOS case-insensitive dosya sistemleri için normalizasyon
    if sys.platform == "win32":
        resolved_check = os.path.normcase(resolved)
        base_check = os.path.normcase(base_resolved)
    elif sys.platform == "darwin":
        # macOS APFS varsayılan olarak case-insensitive, normcase hiçbir şey yapmaz
        resolved_check = resolved.lower()
        base_check = base_resolved.lower()
    else:
        resolved_check = resolved
        base_check = base_resolved

    common = os.path.commonpath([resolved_check, base_check])
    if common != base_check:
        raise ValueError(f"Proje dizini dışına erişim engellendi: {path}")

    if must_exist and not os.path.exists(resolved):
        raise FileNotFoundError(f"Dosya bulunamadı: {resolved}")

    return resolved
