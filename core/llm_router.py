"""Ollama LLM yönlendirici – üretim seviyesinde."""
import ollama  # type: ignore
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from utils.logger import Logger


class LLMRouter:
    def __init__(self, model: str, timeout: int = 30, logger: "Logger | None" = None) -> None:
        self.model = model
        self.timeout = timeout
        self.logger = logger
        self._client = ollama.Client(timeout=timeout)
        self._check_model_exists()

    def _log(self, level: str, msg: str) -> None:
        if self.logger:
            getattr(self.logger, level)(msg)

    def _check_model_exists(self) -> None:
        """Seçilen modelin Ollama'da yüklü olup olmadığını kontrol eder."""
        try:
            models = self._client.list()
            model_names = [m.get("name", "") for m in models.get("models", [])]
            # Kısmi eşleşme: "llama3" -> "llama3.2:3b" veya "llama3:latest" ile eşleşsin
            if not any(self.model in m for m in model_names):
                self._log("warning", f"'{self.model}' modeli Ollama'da bulunamadı. 'ollama pull {self.model}' ile yükleyin.")
        except Exception as e:
            self._log("warning", f"Model listesi alınamadı: {e}")

    def chat(self, messages: list, options: dict | None = None) -> str:
        """LLM'e mesaj gönderir, yanıtı döner."""
        kwargs = {
            "model": self.model,
            "messages": messages,
        }
        if options:
            kwargs["options"] = options
        try:
            response = self._client.chat(**kwargs)
            return response.get("message", {}).get("content", "")
        except Exception as e:
            self._log("error", f"LLM çağrısı başarısız: {e}")
            return ""
