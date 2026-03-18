from abc import ABC, abstractmethod
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, system: str | None = None) -> str:
        pass


class OpenAIProvider(BaseLLMProvider):
    def generate(self, prompt: str, system: str | None = None) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=settings.LLM_API_KEY)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=messages,
        )
        return response.choices[0].message.content


class AnthropicProvider(BaseLLMProvider):
    def generate(self, prompt: str, system: str | None = None) -> str:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.LLM_API_KEY)
        kwargs = {
            "model": settings.LLM_MODEL,
            "max_tokens": 2048,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        response = client.messages.create(**kwargs)
        return response.content[0].text


class OllamaProvider(BaseLLMProvider):
    def generate(self, prompt: str, system: str | None = None) -> str:
        base_url = settings.OLLAMA_BASE_URL
        payload = {
            "model": settings.LLM_MODEL,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system
        response = requests.post(f"{base_url}/api/generate", json=payload, timeout=60)
        response.raise_for_status()
        return response.json()["response"]


def get_llm_provider() -> BaseLLMProvider:
    """Factory: reads LLM_PROVIDER env var and returns appropriate provider."""
    provider = settings.LLM_PROVIDER.lower()
    if provider == 'anthropic':
        return AnthropicProvider()
    elif provider == 'ollama':
        return OllamaProvider()
    else:
        return OpenAIProvider()
