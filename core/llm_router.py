from core.determinism_guard import DeterminismGuard
"""Ollama LLM yönlendirici – üretim seviyesinde."""
import time
import ollama  # type: ignore
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from utils.logger import Logger
from core.uncertainty_filter import apply_filter


class LLMRouter:
    def __init__(self, model: str, timeout: int = 30, logger: "Logger | None" = None) -> None:
        self.model = model
        self.timeout = timeout
        self.logger = logger
        self._client = ollama.Client(timeout=timeout)
        self._default_options = {"temperature": 0.1, "seed": 42}
        self._check_model_exists()

    def _log(self, level: str, msg: str) -> None:
        if self.logger:
            getattr(self.logger, level)(msg)

    def _check_model_exists(self) -> None:
        """Seçilen modelin Ollama'da yüklü olup olmadığını kontrol eder."""
        try:
            models = self._client.list()
            model_names = [m.get("name", "") for m in models.get("models", [])]
            if not any(self.model in m for m in model_names):
                self._log("warning", f"'{self.model}' modeli Ollama'da bulunamadı. 'ollama pull {self.model}' ile yükleyin.")
        except Exception as e:
            self._log("warning", f"Model listesi alınamadı: {e}")

    def chat(self, messages: list, options: dict | None = None,
             retry: int = 2) -> str:
        """LLM'e mesaj gönderir, yanıtı döner.
        Geçici hatalarda retry kadar yeniden dener."""
        merged_options = {**self._default_options}
        if options:
            merged_options.update(options)

        kwargs = {
            "model": self.model,
            "messages": messages,
            "options": merged_options,
        }

        last_error = ""
        diag = RuntimeDiagnostics()
        if diag._initialized:
            diag.increment("llm_calls")
        for attempt in range(retry + 1):
            try:
                response = self._client.chat(**kwargs)
                content = response.get("message", {}).get("content", "")
                if self._uncertainty_enabled():
                    DeterminismGuard().check(messages, self.model, content)
                return apply_filter(content)
                DeterminismGuard().check(messages, self.model, content)
                return content
            except Exception as e:
                last_error = str(e)
                if attempt < retry:
                    if diag._initialized:
                        diag.increment("llm_retries")
                    self._log("warning",
                        f"LLM çağrısı başarısız (deneme {attempt+1}/{retry+1}), "
                        f"yeniden deneniyor: {e}")
                    time.sleep(2 ** attempt * 0.5)
                else:
                    if diag._initialized:
                        diag.increment("llm_errors")
                    self._log("error", f"LLM çağrısı başarısız ({retry+1} deneme): {e}")
        return ""

    def _uncertainty_enabled(self) -> bool:
        """Config üzerinden filtre durumunu oku. Asla çökmez, varsayılan False."""
        try:
            from utils.config import Config
            return Config()._data.get("ENABLE_UNCERTAINTY_FILTER", False)
        except Exception:
            return False
