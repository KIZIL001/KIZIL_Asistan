
"""KIZIL Asistan - Deterministik Prompt Firewall."""
import re
from typing import Optional

BLACKLIST_PATTERNS = [
    (re.compile(r"(?i)ignore\s+(all\s+)?(previous|above)\s+(instructions|prompts?)"), "Önceki talimatları yok sayma"),
    (re.compile(r"(?i)you\s+are\s+(now\s+)?(a\s+)?(different|new|another)"), "Rol değiştirme girişimi"),
    (re.compile(r"(?i)pretend\s+(you\s+are|to\s+be)"), "Rol yapma girişimi"),
    (re.compile(r"(?i)forget\s+(all|everything|your\s+training)"), "Hafıza silme girişimi"),
    (re.compile(r"(?i)system\s*:\s*override"), "Sistem override girişimi"),
    (re.compile(r"(?i)prompt\s*:\s*injection"), "Prompt injection etiketi"),
    (re.compile(r"(?i)dan\s*(\d+|mode|jailbreak)"), "DAN jailbreak girişimi"),
    (re.compile(r"(?i)developer\s*mode"), "Developer mode girişimi"),
    (re.compile(r"(.)\1{99,}"), "Aşırı tekrarlayan karakter spam'i (100+ aynı karakter)"),
]

MAX_INPUT_LENGTH = 8000

def check_firewall(text: str) -> Optional[str]:
    if not text:
        return None
    if len(text) > MAX_INPUT_LENGTH:
        return f"[REDDEDİLDİ] Girdi çok uzun ({len(text)} > {MAX_INPUT_LENGTH} karakter). Lütfen daha kısa bir mesaj gönderin."
    for pattern, desc in BLACKLIST_PATTERNS:
        if pattern.search(text):
            return f"[REDDEDİLDİ] {desc} tespit edildi. Bu işlem güvenlik nedeniyle engellendi."
    return None
