"""Araç çıktılarını deterministik olarak doğrula."""
import re
from typing import Optional

def verify_tool_output(tool_name: str, result: str) -> Optional[str]:
    """Araç sonucunu doğrular, hata varsa uyarı döner, yoksa None."""
    if not result:
        return "[Araç hatası] Boş sonuç"
    
    # Matematiksel işlem araçları
    if tool_name in ("hesapla", "calculate", "math"):
        # Sayısal sonuç bekleriz
        if not re.search(r'\d', result):
            return "[Araç hatası] Sayısal sonuç bekleniyordu"
    
    # Dosya okuma araçları
    if tool_name in ("dosya_oku", "read_file", "oku"):
        if "[HATA]" in result:
            return None  # Hata zaten işaretlenmiş
    
    # Tarih/saat araçları
    if tool_name in ("tarih", "saat", "datetime", "date", "time"):
        if not re.search(r'\d{2}[:.]\d{2}', result) and not re.search(r'\d{4}', result):
            return "[Araç hatası] Geçerli tarih/saat formatı bulunamadı"
    
    # Sistem komutu araçları
    if tool_name in ("sistem", "system", "komut", "command"):
        if len(result) > 10000:
            return f"[Araç hatası] Aşırı uzun çıktı ({len(result)} karakter)"
    
    # HTML/Web araçları
    if tool_name in ("web_get", "http_get", "fetch"):
        if result.startswith("[HATA]"):
            return None
    
    # Varsayılan: geçerli
    return None
