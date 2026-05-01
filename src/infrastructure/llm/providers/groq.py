import opik
from openai import OpenAI

from src.config import get_settings
from src.infrastructure.llm.interface import LLMInterface


class _StructuredGroqLLM:
    def __init__(self, client: OpenAI, model_name: str, schema) -> None:
        self.client = client
        self.model_name = model_name
        self.schema = schema

    @opik.track(name="groq.structured_invoke", type="llm", flush=True)
    def invoke(self, messages: list):
        completion = self.client.beta.chat.completions.parse(
            model=self.model_name,
            messages=messages,
            response_format=self.schema,
        )
        return completion.choices[0].message.parsed


class GroqLLMProvider(LLMInterface):
    def __init__(self, client: OpenAI, model_name: str | None = None) -> None:
        settings = get_settings()
        self.client = client
        self.model_name = model_name or settings.llm_model.name

    def connect(self):
        return self.client

    def disconnect(self):
        self.client.close()

    @opik.track(name="groq.chat", type="llm", flush=True)
    def chat(self, messages: list, **kwargs):
        return self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            **kwargs,
        )

    def with_structured_output(self, schema):
        return _StructuredGroqLLM(self.client, self.model_name, schema)
