"""Merkezi güvenli yol denetimi – tüm modüller için ortak."""
import os


def safe_path(path: str, base_dir: str | None = None) -> str:
    """
    Yolu mutlak yapar, sembolik bağları çözer, proje dizini dışına çıkmayı engeller.
    """
    if not path:
        raise ValueError("Yol boş olamaz.")
    resolved = os.path.realpath(os.path.abspath(path))
    parts = resolved.replace("\\", "/").split("/")
    if ".." in parts:
        raise ValueError("Yol '..' içeremez.")
    if base_dir is None:
        base_dir = os.getcwd()
    base_resolved = os.path.realpath(os.path.abspath(base_dir))
    common = os.path.commonpath([resolved, base_resolved])
    if common != base_resolved:
        raise ValueError(f"Proje dizini dışına erişim engellendi: {path}")
    return resolved
