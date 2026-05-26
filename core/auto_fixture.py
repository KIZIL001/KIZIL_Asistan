"""
Auto‑Fixture Suggestion – Anomali girdilerden fixture adayı toplar.
Yeni capability değildir; yalnızca mevcut hataları kaydeder.
Maksimum 50 öneri (FIFO) ile sınırlıdır.
"""
import json, os
from utils.file_utils import atomic_write_json, atomic_read_json

SUGGESTION_FILE = "storage/fixture_suggestions.json"
MAX_SUGGESTIONS = 50

def suggest(input_text: str, reason: str):
    suggestions = atomic_read_json(SUGGESTION_FILE, [])
    suggestions.append({"input": input_text, "reason": reason})
    if len(suggestions) > MAX_SUGGESTIONS:
        suggestions = suggestions[-MAX_SUGGESTIONS:]  # FIFO: en eski uçar
    try:
        atomic_write_json(SUGGESTION_FILE, suggestions)
    except Exception:
        pass  # öneri kaydedilemezse sistem çökmez
