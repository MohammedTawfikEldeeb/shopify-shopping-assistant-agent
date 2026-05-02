from langchain_openai import ChatOpenAI

from src.config import get_settings


def make_langchain_llm(temperature: float = 0.7) -> ChatOpenAI:
    settings = get_settings()
    provider = settings.llm.provider.lower()

    if provider == "groq":
        return ChatOpenAI(
            model=settings.llm_model.name,
            api_key=settings.groq_api.key,
            base_url=settings.groq_api.base_url,
            temperature=temperature,
        )

    if provider == "openrouter":
        return ChatOpenAI(
            model=settings.llm_model.name,
            api_key=settings.openrouter_api.key,
            base_url=settings.openrouter_api.base_url,
            temperature=temperature,
        )

    raise ValueError(f"Unsupported LLM provider: {settings.llm.provider}")
