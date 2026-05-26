"""
Telemetry Archive & Dashboard – Terminal tabanlı operasyonel sağlık paneli.
Yalnızca okur (read-only), safe_call ile sarılıdır, asla çökmez.
"""
import json
import os
from core.safe_failures import safe_call

STORAGE = "storage"

def _read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _read_last_lines(path, count=3):
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return "".join(lines[-count:])

def get_panel() -> str:
    """Tüm metrikleri topla, formatlanmış panel metni döndür."""
    lines = []
    lines.append("=" * 60)
    lines.append("  KIZIL Asistan – Operasyonel Sağlık Paneli")
    lines.append("=" * 60)

    # Stability Watchdog
    wd = safe_call(_read_json, f"{STORAGE}/stability_watchdog.json",
                   fallback={}, context="watchdog")
    lines.append("  Toplam Oturum    : " + str(wd.get('total_sessions', '[VERI YOK]')))
    lines.append("  Anormal Kapanış  : " + str(wd.get('total_crashes', '[VERI YOK]')))
    uptime = wd.get('total_uptime_seconds', 0)
    lines.append("  Toplam Uptime    : {}s {}dk".format(uptime//3600, (uptime%3600)//60))

    # Determinizm Skoru
    metrics = safe_call(_read_json, f"{STORAGE}/metrics.json",
                        fallback={}, context="metrics")
    det_skor = metrics.get("determinizm_skoru", None)
    if det_skor is not None:
        lines.append("  Determinizm Skoru: %{}".format(round(det_skor*100, 1)))
    else:
        lines.append("  Determinizm Skoru: [VERI YOK]")

    # Araç Başarı Oranı
    toplam = metrics.get("toplam_arac_cagrisi", 0)
    basarili = metrics.get("basarili_arac_cagrisi", 0)
    if toplam > 0:
        oran = round(basarili/toplam*100, 1)
        lines.append("  Araç Başarı Oranı: %{} ({}/{})".format(oran, basarili, toplam))
    else:
        lines.append("  Araç Başarı Oranı: [VERI YOK]")

    # Config Drift
    from utils.config import Config
    cfg = Config()
    drift_var = safe_call(cfg.detect_drift, fallback="[KONTROL EDİLEMEDİ]", context="config_drift")
    drift_str = "VAR" if drift_var else "YOK" if drift_var is False else str(drift_var)
    lines.append("  Config Drift      : " + drift_str)

    # Aktif Refinement Modülleri
    mods = []
    for key in sorted(cfg._data.keys()):
        if key.startswith("ENABLE_") and cfg._data[key]:
            mods.append(key.replace("ENABLE_", "").lower())
    lines.append("  Aktif Modüller    : " + (", ".join(mods) if mods else "[HICBIRI]"))

    # Son Hatalar
    errors = safe_call(_read_last_lines, f"{STORAGE}/kizil.log", 3,
                       fallback="[HATA LOGU YOK]", context="error_log")
    lines.append("  Son Hata Satırları:
" + (errors.strip() if errors else "[YOK]"))

    lines.append("=" * 60)
    return "
".join(lines)
