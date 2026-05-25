"""Kural tabanlı halüsinasyon azaltma filtresi. Model iç sinyallerine erişmez, tamamen deterministik."""
import re
import json
from pathlib import Path
from typing import List, Tuple

TRUSTED_FACTS_PATH = Path(__file__).parent.parent / "data" / "trusted_facts.json"

def _load_trusted_facts() -> dict:
    """Güvenilir bilgi kırıntılarını yükle. Hata durumunda boş dön, asla çökme."""
    try:
        if TRUSTED_FACTS_PATH.exists():
            with open(TRUSTED_FACTS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError, OSError):
        pass
    return {}

TRUSTED_FACTS = _load_trusted_facts()

# Desenler: (regex, kategori)
PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\b\d{4}\b"), "tarih"),
    (re.compile(r"\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*(?:milyon|milyar|bin|yüzde|%)\b"), "büyük sayı/yüzde"),
    (re.compile(r"\b\d{2}\.\d{2}\.\d{4}\b"), "tarih"),
    (re.compile(r"\b(?:kesinlikle|asla|her zaman|hiçbir zaman|tam olarak)\b"), "kesinlik ifadesi"),
    (re.compile(r"\b\d+\s*(?:kg|km|m|cm|mm|lt|ml|gb|mb|tb)\b"), "ölçü birimi"),
]

def _normalize(value: str) -> str:
    """Fazla boşlukları tek boşluğa indir, baştaki/sondakileri temizle."""
    return " ".join(value.split())

def apply_filter(text: str) -> str:
    """Metindeki doğrulanamayan sayısal/kesin ifadeleri [Kesin değil] ile etiketle."""
    if not text:
        return text
    
    alerts: List[str] = []
    for pattern, kategori in PATTERNS:
        for match in pattern.finditer(text):
            raw_value = match.group()
            if kategori in ("tarih", "büyük sayı/yüzde", "ölçü birimi"):
                normalized = _normalize(raw_value)
                if normalized not in TRUSTED_FACTS.get(kategori, []):
                    alerts.append(f"[Kesin değil] {raw_value}")
            elif kategori == "kesinlik ifadesi":
                alerts.append(f"[Kesin değil] {raw_value}")
    
    if not alerts:
        return text
    
    alert_str = " ".join(alerts)
    return f"{alert_str}\n{text}"
