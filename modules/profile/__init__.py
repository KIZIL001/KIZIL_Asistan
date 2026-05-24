"""Kullanıcı profili yönetimi."""
import os
import json
from utils.config import Config


class ProfileManager:
    def __init__(self):
        self.config = Config()
        self.file = os.path.join(self.config.STORAGE_DIR, "profile.json")
        self._data = self._load()

    def _defaults(self) -> dict:
        return {
            "ad": "",
            "tercihler": {},
            "notlar": "",
            "model": self.config.LLM_MODEL,
        }

    def _load(self) -> dict:
        if os.path.exists(self.file):
            try:
                with open(self.file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Eksik anahtarları varsayılanla tamamla
                defaults = self._defaults()
                for k, v in defaults.items():
                    if k not in data:
                        data[k] = v
                return data
            except (json.JSONDecodeError, IOError):
                pass
        return self._defaults()

    def save(self):
        with open(self.file, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value):
        self._data[key] = value
        self.save()

    def get_all(self) -> dict:
        return dict(self._data)

    def get_prompt(self) -> str:
        """LLM'e tanıtılacak profil metni."""
        parts = []
        if self._data.get("ad"):
            parts.append(f"Kullanıcının adı: {self._data['ad']}.")
        if self._data.get("tercihler"):
            tercihler = self._data["tercihler"]
            if tercihler:
                t_str = ", ".join(f"{k}: {v}" for k, v in tercihler.items())
                parts.append(f"Kullanıcının tercihleri: {t_str}.")
        if self._data.get("notlar"):
            parts.append(f"Kullanıcı hakkında notlar: {self._data['notlar']}.")
        if parts:
            return "KULLANICI PROFİLİ:\n" + "\n".join(parts)
        return ""

    def update_from_summary(self, summary: str):
        """Özet metninden profil bilgisi çıkarmaya çalışır (basit)."""
        summary_lower = summary.lower()
        if not self._data.get("ad") and "adı" in summary_lower:
            # Basit bir isim yakalama denemesi yok, LLM'e bırak
            pass
        # Şimdilik sadece notlar kısmına ekle
        if self._data.get("notlar"):
            self._data["notlar"] += "\n" + summary
        else:
            self._data["notlar"] = summary
        self.save()
