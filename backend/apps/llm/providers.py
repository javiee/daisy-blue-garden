from abc import ABC, abstractmethod
import base64
import logging
import mimetypes
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class VisionNotSupportedError(Exception):
    """Raised when an image is sent to a provider that cannot process images."""
    pass


class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, system: str | None = None, image_path: str | None = None) -> str:
        pass


class OpenAIProvider(BaseLLMProvider):
    def generate(self, prompt: str, system: str | None = None, image_path: str | None = None) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=settings.LLM_API_KEY)
        if image_path is not None:
            content = [{'type': 'text', 'text': prompt}]
            with open(image_path, 'rb') as f:
                image_b64 = base64.b64encode(f.read()).decode('ascii')
            mime = mimetypes.guess_type(image_path)[0] or 'image/jpeg'
            content.append({
                'type': 'image_url',
                'image_url': {'url': f'data:{mime};base64,{image_b64}'},
            })
        else:
            content = prompt
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": content})
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=messages,
        )
        return response.choices[0].message.content


class AnthropicProvider(BaseLLMProvider):
    def generate(self, prompt: str, system: str | None = None, image_path: str | None = None) -> str:
        if image_path is not None:
            raise VisionNotSupportedError("Anthropic provider does not support image input yet")
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
    def generate(self, prompt: str, system: str | None = None, image_path: str | None = None) -> str:
        if image_path is not None:
            raise VisionNotSupportedError("Ollama provider does not support image input yet")
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
