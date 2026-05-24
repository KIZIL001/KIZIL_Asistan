"""Araç kayıt, ayrıştırma ve çalıştırma yöneticisi."""
import re
import json
import inspect
from typing import Any, Callable, Optional


class ToolManager:
    """Araçları kaydeder, LLM çıktısından çağrıları ayrıştırır ve çalıştırır."""

    def __init__(self) -> None:
        self.tools: dict[str, dict[str, Any]] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: dict[str, str],
        func: Callable[..., str],
    ) -> None:
        """Yeni bir araç kaydeder."""
        self.tools[name] = {
            "description": description,
            "parameters": parameters,
            "func": func,
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
            try:
                params = json.loads(raw_params.strip()) if raw_params.strip() else {}
            except json.JSONDecodeError:
                first_line = raw_params.strip().split("\n")[0]
                params = {"input": first_line} if first_line else {}
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
