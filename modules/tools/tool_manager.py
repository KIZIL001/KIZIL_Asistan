"""Araç kayıt, ayrıştırma ve çalıştırma yöneticisi."""
import re
import json
import inspect
from typing import Any, Callable, Optional


class ToolManager:
    MAX_PARAM_CHARS = 65536
    """Araçları kaydeder, LLM çıktısından çağrıları ayrıştırır ve çalıştırır."""

    def __init__(self) -> None:
        self.tools: dict[str, dict[str, Any]] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: dict[str, str],
        func: Callable[..., str],
        timeout: Optional[int] = None,
    ) -> None:
        """Yeni bir araç kaydeder. timeout (saniye) opsiyonel, ileride kullanılacak."""
        self.tools[name] = {
            "description": description,
            "parameters": parameters,
            "func": func,
            "timeout": timeout,  # Pasif: şimdilik sadece saklanır
        }

    def get_tool_list(self) -> str:
        """LLM'e gönderilecek araç listesi metnini oluşturur."""
        lines = []
        for name, info in self.tools.items():
            params = ", ".join(info["parameters"].keys())
            lines.append(f"- {name}({params}): {info['description']}")
        return "\n".join(lines)

    def _filter_params(self, func: Callable, raw: dict) -> dict:
        """Fonksiyonun kabul ettiği parametreleri al, sadece onları geçir."""
        sig = inspect.signature(func)
        valid = {}
        for key, value in raw.items():
            if key in sig.parameters:
                valid[key] = value
        return valid

    def parse_and_execute(self, text: str) -> Optional[str]:
        """Metin içinde [TOOL_CALL:araç_adı] ... bulursa çalıştırır, sonucu döner."""
        pattern = r"\[TOOL_CALL:(\w+)\]\s*(.*?)(?=\[TOOL_CALL|\Z)"
        matches = re.findall(pattern, text, re.DOTALL)
        results = []
        for tool_name, raw_params in matches:
            if tool_name not in self.tools:
                results.append(f"[HATA] '{tool_name}' aracı bulunamadı.")
                continue
            # H2-3: Parametre güvenlik kontrolleri
            raw_stripped = raw_params.strip()
            if len(raw_stripped) > self.MAX_PARAM_CHARS:
                results.append(f"[HATA] Parametre çok büyük ({len(raw_stripped)} > {self.MAX_PARAM_CHARS} karakter), reddedildi.")
                continue
            if "\x00" in raw_stripped or "\\x00" in raw_stripped:
                results.append("[HATA] Parametre null byte içeriyor, reddedildi.")
                continue
            raw_clean = raw_stripped.replace("\\x00", "").replace("\x00", "")
            try:
                params = json.loads(raw_clean) if raw_clean else {}
            except json.JSONDecodeError:
                snippet = raw_params.strip()[:80]
                results.append(f"[HATA] JSON bozuk, çağrı atlandı: {snippet}...")
                continue
            try:
                func = self.tools[tool_name]["func"]
                filtered = self._filter_params(func, params)
                result = func(**filtered)
                results.append(f"[ARAÇ: {tool_name}]\n{result}")
            except Exception as e:
                results.append(f"[HATA] Araç çalışırken hata: {e}")
        return "\n\n".join(results) if results else None

    def has_tool_call(self, text: str) -> bool:
        """Metinde araç çağrısı var mı?"""
        return bool(re.search(r"\[TOOL_CALL:\w+\]", text))
