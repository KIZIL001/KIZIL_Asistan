"""
Behavioral Drift Detector – Yanıt stili/uzunluğu sapmalarını izler.
Yeni capability değildir; yalnızca mevcut çıktıyı ölçer.
Disk G/Ç yalnızca oturum sonunda yapılır.
"""
import json, os

DRIFT_FILE = "storage/behavioral_drift.json"
_data = {"lengths": [], "avg": 0.0, "count": 0, "last_drift": 0.0}
_last_text = None

def record_response(text: str) -> float:
    """Yanıtı RAM'deki kayan ortalamaya ekler, drift skoru döndürür."""
    global _data, _last_text
    if text == _last_text:
        return _data["last_drift"]
    _last_text = text
    length = len(text)
    n = _data["count"]
    old_avg = _data["avg"]
    new_avg = (old_avg * n + length) / (n + 1) if n > 0 else length
    drift = abs(length - old_avg) / max(old_avg, 1) if n > 0 else 0.0
    drift = min(drift, 1.0)
    _data["lengths"].append(length)
    _data["avg"] = new_avg
    _data["count"] = n + 1
    _data["last_drift"] = round(drift, 3)
    if len(_data["lengths"]) > 100:
        _data["lengths"] = _data["lengths"][-100:]
    return drift

def save_to_disk():
    """RAM'deki veriyi diske yazar. orchestrator.stop() içinden çağrılır."""
    os.makedirs(os.path.dirname(DRIFT_FILE), exist_ok=True)
    with open(DRIFT_FILE, "w", encoding="utf-8") as f:
        json.dump(_data, f, indent=2)
