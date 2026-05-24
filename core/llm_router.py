"""Ollama LLM yönlendirici."""
import ollama  # type: ignore


class LLMRouter:
    def __init__(self, model: str) -> None:
        self.model = model

    def chat(self, messages: list) -> str:
        response = ollama.chat(model=self.model, messages=messages)
        return response.get("message", {}).get("content", "")
