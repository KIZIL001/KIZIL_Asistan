"""
Veri bütünlüğü doğrulama ve kısmi kurtarma.
Kritik dosyalar (config.json, release.json) bozuksa safe‑mode tetiklenir.
Operasyonel dosyalarda bozuk alanlar atlanır, kalan veri kurtarılır.
"""
import json
import os
import hashlib

CRITICAL_FILES = ["storage/config.json", "storage/release.json"]
OPERATIONAL_FILES = ["storage/tasks.json", "storage/profile.json"]

def _compute_hash(data: dict) -> str:
    raw = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]

def validate_json(path: str) -> dict | None:
    """Dosyayı JSON olarak açar; bozuksa None döner (binary)."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, (dict, list)):
            return None
        return data
    except (json.JSONDecodeError, OSError):
        return None

def check_critical_files() -> bool:
    """Kritik dosyalar sağlamsa True, en az biri bozuksa False."""
    for f in CRITICAL_FILES:
        if validate_json(f) is None:
            return False
    return True

def recover_operational(path: str) -> dict | list | None:
    """Operasyonel JSON'u kısmen kurtarır (en üst seviye dict/list kalırsa)."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
        # Satır satır dene: son geçerli JSON noktasına kadar al
        for i in range(len(raw), 0, -1):
            try:
                data = json.loads(raw[:i])
                if isinstance(data, (dict, list)):
                    return data
            except json.JSONDecodeError:
                continue
        return None
    except OSError:
        return None

def repair_operational(path: str) -> bool:
    """Operasyonel dosyayı kısmen onarır, başarılıysa üzerine yazar."""
    recovered = recover_operational(path)
    if recovered is not None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(recovered, f, indent=2, ensure_ascii=False)
        return True
    return False

def inject_schema_version(path: str, version: str = "1.0") -> None:
    """JSON dosyasına schema_version alanını ekler (yoksa)."""
    data = validate_json(path)
    if data is None:
        return
    if isinstance(data, dict) and "schema_version" not in data:
        data["schema_version"] = version
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
