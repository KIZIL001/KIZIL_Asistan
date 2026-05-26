"""KIZIL Asistan - Recovery (Kurtarma) Aracı.
Bozuk kritik dosyaları fabrika varsayılanlarına döndürür.
Sadece safe-mode aktifken veya manuel çağrıldığında çalışır.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from utils.file_utils import atomic_write_json, atomic_read_json
from core.safe_mode import disable_safe_mode, check_integrity

FACTORY_DEFAULTS = {
    "storage/release.json": {
        "version": "1.1.0",
        "phase": "production-engineering",
        "release_date": "2026-05-26",
        "runtime": "sequential-deterministic",
        "production_freeze": True,
    },
    "storage/config.json": {
        "LLM_MODEL": "phi3:mini",
        "LOG_LEVEL": "INFO",
        "SUMMARY_MAX_LINES": 200,
        "STORAGE_DIR": "storage",
        "LOG_FILE": "kizil.log",
        "CONVERSATIONS_DIR": "conversations",
        "MEMORY_DIR": "memory",
        "ENABLE_UNCERTAINTY_FILTER": False,
        "ENABLE_DECISION_TRACE": False,
        "ENABLE_CONTEXT_POISONING_DEFENSE": False,
        "ENABLE_JACCARD_PRUNING": False,
        "ENABLE_RESPONSE_TEMPLATES": False,
        "ENABLE_TOOL_VERIFICATION": False,
        "ENABLE_PROMPT_FIREWALL": False,
        "ENABLE_FAILURE_CORPUS": False,
        "ENABLE_GOLDEN_SESSION_RECORDING": False,
        "ENABLE_RUNTIME_DIAGNOSTICS": False,
        "ENABLE_DETERMINISM_GUARD": False,
        "ENABLE_TOOL_RELIABILITY": False,
        "ENABLE_PROMPT_DISCIPLINE": False,
    }
}


def recover_all():
    """Tüm kritik dosyaları fabrika varsayılanlarına döndür."""
    for path, default_data in FACTORY_DEFAULTS.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        mevcut = atomic_read_json(path, {})
        # Mevcut değerleri koru, eksikleri ekle
        if isinstance(mevcut, dict) and isinstance(default_data, dict):
            merged = {**default_data, **mevcut}
        else:
            merged = default_data
        atomic_write_json(path, merged)
        print(f"  ✓ {path} kurtarıldı")


if __name__ == "__main__":
    print("KIZIL Recovery Aracı")
    print("=" * 40)
    if check_integrity():
        print("Tüm kritik dosyalar sağlam görünüyor.")
        print("Yine de fabrika varsayılanlarına dönmek istiyor musunuz? (e/h): ", end="")
        cevap = input().strip().lower()
        if cevap in ("e", "evet", "y", "yes"):
            recover_all()
            print("Kurtarma tamamlandı.")
        else:
            print("İptal edildi.")
    else:
        print("Bozuk kritik dosyalar tespit edildi. Kurtarma başlatılıyor...")
        recover_all()
        disable_safe_mode()
        print("Kurtarma tamamlandı. Safe-mode devre dışı bırakıldı.")
