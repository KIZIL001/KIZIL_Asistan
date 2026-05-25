"""KIZIL Prompt Discipline - Bellek ici drift takibi, esnek on ek kontrolu."""
import json, re
from pathlib import Path
from typing import Optional

class PromptDiscipline:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_ready'):
            self._ready = True
            self._templates_path = Path("data/response_templates.json")
            self._log_dir = Path("storage/diagnostics")
            self._log_dir.mkdir(parents=True, exist_ok=True)
            self._drifts = []  # Bellek ici birikim
            self._load_templates()

    def _is_enabled(self):
        from utils.config import Config
        return Config()._data.get("ENABLE_PROMPT_DISCIPLINE", False)

    def _load_templates(self):
        if self._templates_path.exists():
            self._templates = json.loads(self._templates_path.read_text())
        else:
            self._templates = {}

    def check(self, user_msg: str, response: str) -> Optional[str]:
        if not self._is_enabled():
            return None
        
        for name, tpl in self._templates.items():
            if re.search(tpl["pattern"], user_msg):
                expected = tpl["template"].replace("{cevap}", "").strip()
                clean_response = response.strip()
                if expected and not clean_response.startswith(expected[:5]):
                    self._add_drift(name, user_msg, clean_response, expected)
                    return name
        return None

    def _add_drift(self, template_name: str, user_msg: str, response: str, expected: str):
        self._drifts.append({
            "template": template_name,
            "user_msg": user_msg[:200],
            "response": response[:200],
            "expected_prefix": expected[:100]
        })

    def save(self):
        if not self._drifts:
            return
        from datetime import datetime
        data = {
            "timestamp": datetime.now().isoformat(),
            "type": "TEMPLATE_DRIFT_BATCH",
            "count": len(self._drifts),
            "drifts": self._drifts
        }
        fname = f"drift_batch_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
        (self._log_dir / fname).write_text(json.dumps(data, indent=2, ensure_ascii=False))
        self._drifts.clear()
