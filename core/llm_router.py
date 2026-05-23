import ollama

class LLMRouter:
    """Farklı dil modellerine yönlendirme yapar. Şimdilik sadece Ollama."""

    def __init__(self, model="phi3:mini"):
        self.model = model

    def chat(self, messages):
        """Modelle sohbet et, yanıt metnini döndür."""
        try:
            response = ollama.chat(model=self.model, messages=messages)
            return response["message"]["content"].strip()
        except Exception as e:
            raise RuntimeError(f"LLM çağrısı başarısız: {e}")