from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings


class OpenAIProviderTest(TestCase):
    @override_settings(LLM_API_KEY='test-key', LLM_MODEL='gpt-4o')
    @patch('apps.llm.providers.OpenAI')
    def test_generate(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content='response text'))]
        )
        from apps.llm.providers import OpenAIProvider
        provider = OpenAIProvider()
        result = provider.generate('test prompt', system='system')
        self.assertEqual(result, 'response text')


class AnthropicProviderTest(TestCase):
    @override_settings(LLM_API_KEY='test-key', LLM_MODEL='claude-sonnet-4-6')
    @patch('apps.llm.providers.anthropic')
    def test_generate(self, mock_anthropic):
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text='response text')]
        )
        from apps.llm.providers import AnthropicProvider
        provider = AnthropicProvider()
        result = provider.generate('test prompt')
        self.assertEqual(result, 'response text')


class OllamaProviderTest(TestCase):
    @override_settings(OLLAMA_BASE_URL='http://localhost:11434', LLM_MODEL='llama3.2')
    @patch('apps.llm.providers.requests.post')
    def test_generate(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {'response': 'ollama response'}
        )
        mock_post.return_value.raise_for_status = MagicMock()
        from apps.llm.providers import OllamaProvider
        provider = OllamaProvider()
        result = provider.generate('test prompt')
        self.assertEqual(result, 'ollama response')


class GetLLMProviderTest(TestCase):
    @override_settings(LLM_PROVIDER='openai')
    def test_returns_openai(self):
        from apps.llm.providers import get_llm_provider, OpenAIProvider
        self.assertIsInstance(get_llm_provider(), OpenAIProvider)

    @override_settings(LLM_PROVIDER='anthropic')
    def test_returns_anthropic(self):
        from apps.llm.providers import get_llm_provider, AnthropicProvider
        self.assertIsInstance(get_llm_provider(), AnthropicProvider)

    @override_settings(LLM_PROVIDER='ollama')
    def test_returns_ollama(self):
        from apps.llm.providers import get_llm_provider, OllamaProvider
        self.assertIsInstance(get_llm_provider(), OllamaProvider)
