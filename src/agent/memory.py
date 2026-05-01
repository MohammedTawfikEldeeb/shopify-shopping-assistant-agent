class ShortTermMemory:
    def __init__(self):
        self.last_product_ids: list[str] = []
        self.last_products: list[dict] = []
        self.summary: str = ""
        self.messages: list[dict] = []

    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})

    def should_summarize(self) -> bool:
        return len(self.messages) >= 8

    def get_context(self) -> str:
        parts = []
        if self.summary:
            parts.append(f"Previous conversation summary: {self.summary}")
        if len(self.messages) > 2:
            for msg in self.messages[:-2]:
                parts.append(f"{msg['role'].capitalize()}: {msg['content']}")
        if len(self.messages) >= 2:
            parts.append("Recent messages:")
            for msg in self.messages[-2:]:
                parts.append(f"{msg['role'].capitalize()}: {msg['content']}")
        elif self.messages:
            parts.append("Current message:")
            for msg in self.messages:
                parts.append(f"{msg['role'].capitalize()}: {msg['content']}")
        return "\n".join(parts)

    def set_products(self, products: list[dict]):
        self.last_products = products
        self.last_product_ids = [p["id"] for p in products]

    def clear(self):
        self.last_products = []
        self.last_product_ids = []
        self.summary = ""
        self.messages = []
