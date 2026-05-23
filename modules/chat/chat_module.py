from core.llm_router import LLMRouter


class ChatModule:
    def __init__(self, router: LLMRouter):
        self.router = router

    def yanit_ver(self, msg: str, ctx: dict = None) -> str:
        messages = []
        if ctx and "system" in ctx:
            messages.append({"role": "system", "content": ctx["system"]})
        if ctx and "history" in ctx:
            messages.extend(ctx["history"])
        messages.append({"role": "user", "content": msg})
        return self.router.chat(messages)

    def _llm_yanit(self, prompt: str) -> str:
        return self.yanit_ver(msg=prompt)
