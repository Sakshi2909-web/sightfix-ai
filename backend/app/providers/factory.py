from app.config import settings
from app.providers.base import VLMProvider, LLMProvider, EmbeddingProvider
from app.providers.mock import MockVLMProvider, MockLLMProvider, MockEmbeddingProvider
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.local_provider import LocalProvider


def get_vlm_provider() -> VLMProvider:
    choice = (settings.VLM_PROVIDER or "mock").lower()
    if choice == "anthropic" and settings.ANTHROPIC_API_KEY:
        return AnthropicProvider(settings.ANTHROPIC_API_KEY)
    elif choice == "openai" and settings.OPENAI_API_KEY:
        return OpenAIProvider(settings.OPENAI_API_KEY)
    elif choice == "gemini" and settings.GEMINI_API_KEY:
        return GeminiProvider(settings.GEMINI_API_KEY)
    elif choice == "local":
        return LocalProvider()
    return MockVLMProvider()


def get_llm_provider() -> LLMProvider:
    choice = (settings.LLM_PROVIDER or "mock").lower()
    if choice == "anthropic" and settings.ANTHROPIC_API_KEY:
        return AnthropicProvider(settings.ANTHROPIC_API_KEY)
    elif choice == "openai" and settings.OPENAI_API_KEY:
        return OpenAIProvider(settings.OPENAI_API_KEY)
    elif choice == "gemini" and settings.GEMINI_API_KEY:
        return GeminiProvider(settings.GEMINI_API_KEY)
    elif choice == "local":
        return LocalProvider()
    return MockLLMProvider()


def get_embedding_provider() -> EmbeddingProvider:
    choice = (settings.EMBEDDING_PROVIDER or "mock").lower()
    if choice == "openai" and settings.OPENAI_API_KEY:
        return OpenAIProvider(settings.OPENAI_API_KEY)
    elif choice == "local":
        return LocalProvider()
    return MockEmbeddingProvider()
