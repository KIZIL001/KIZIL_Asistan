"""
Safe-mode kontrolü.
Yalnızca binary (0/1) kontroller kullanır; bulanık eşik, skor veya
olasılıksal mekanizma içermez. Deterministik ve yan etkisizdir.
"""
import os
import json

# Kontrol edilecek kritik dosyalar ve minimum geçerlilik koşulları
CRITICAL_FILES = [
    ("storage/config.json", lambda data: isinstance(data, dict)),
    ("storage/release.json", lambda data: isinstance(data, dict) and "version" in data),
]

# Safe-mode bayrağı (ortam değişkeni ile override edilebilir)
SAFE_MODE_FLAG = "storage/.safe_mode"


def check_integrity() -> bool:
    """Kritik dosyaların bütünlüğünü kontrol eder.
    Dönüş: True = sistem sağlıklı, False = safe-mode gerekli.
    """
    for path, validator in CRITICAL_FILES:
        if not os.path.exists(path):
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not validator(data):
                return False
        except (json.JSONDecodeError, OSError):
            return False
    return True


def is_safe_mode() -> bool:
    """Safe-mode aktif mi? (binary dönüş)"""
    if os.path.exists(SAFE_MODE_FLAG):
        return True
    return not check_integrity()


def enable_safe_mode() -> None:
    """Safe-mode'u aktif et."""
    with open(SAFE_MODE_FLAG, "w", encoding="utf-8") as f:
        f.write("1")


def disable_safe_mode() -> None:
    """Safe-mode'u pasif et."""
    if os.path.exists(SAFE_MODE_FLAG):
        os.remove(SAFE_MODE_FLAG)
