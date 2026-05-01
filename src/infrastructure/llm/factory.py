from langsmith.wrappers import wrap_openai
from openai import OpenAI

from src.config import get_settings
from src.infrastructure.llm.enum import LLMProviderEnums
from src.infrastructure.llm.providers.groq import GroqLLMProvider
from src.infrastructure.llm.providers.openrouter import OpenRouterLLMProvider


class LLMFactory:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _create_groq_client(self) -> OpenAI:
        client = OpenAI(
            api_key=self.settings.groq_api.key,
            base_url=self.settings.groq_api.base_url,
        )
        return wrap_openai(client, chat_name="GroqChatCompletions")

    def _create_openrouter_client(self) -> OpenAI:
        client = OpenAI(
            api_key=self.settings.openrouter_api.key,
            base_url=self.settings.openrouter_api.base_url,
        )
        return wrap_openai(client, chat_name="OpenRouterChatCompletions")

    def create(self, provider: LLMProviderEnums | str):
        normalized_provider = provider.value if isinstance(provider, LLMProviderEnums) else str(provider).lower()

        if normalized_provider == LLMProviderEnums.Groq.value:
            return GroqLLMProvider(
                client=self._create_groq_client(),
                model_name=self.settings.llm_model.name,
            )

        if normalized_provider == LLMProviderEnums.OpenRouter.value:
            return OpenRouterLLMProvider(
                client=self._create_openrouter_client(),
                model_name=self.settings.llm_model.name,
            )

        raise ValueError(f"Unsupported LLM provider: {provider}")


def create_llm(provider: LLMProviderEnums | str):
    return LLMFactory().create(provider)
