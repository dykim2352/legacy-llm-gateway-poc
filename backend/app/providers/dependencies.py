from app.core.config import settings
from app.providers.base import LLMProvider
from app.providers.ollama import OllamaProvider


def get_llm_provider() -> LLMProvider:
    return OllamaProvider(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        timeout_seconds=settings.llm_request_timeout_seconds,
    )
